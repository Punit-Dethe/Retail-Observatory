"""Optional model planner over approved retail tools. No arbitrary code execution."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from canvas_analysis import META, build_investigation, guided_plan, unsupported, validate_scope
from canvas_theory import run_agent

ROOT = Path(__file__).resolve().parents[1]


def load_local_environment():
    path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        text = line.strip()
        if not text or text.startswith('#') or '=' not in text:
            continue
        name, value = text.split('=', 1)
        if name.strip().startswith('RETAIL_LLM_'):
            os.environ.setdefault(name.strip(), value.strip().strip('"\''))


load_local_environment()


class ProviderError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def configured():
    return bool(os.environ.get('RETAIL_LLM_MODEL') and os.environ.get('RETAIL_LLM_BASE_URL'))


def capabilities():
    missing = [name for name in ('RETAIL_LLM_BASE_URL', 'RETAIL_LLM_MODEL', 'RETAIL_LLM_API_KEY') if not os.environ.get(name, '').strip()]
    return {'mode': 'llm' if configured() else 'guided', 'llmConfigured': configured(),
            'missingSettings': missing,
            'model': os.environ.get('RETAIL_LLM_MODEL') if configured() else None,
            'source': 'Online Retail II', 'start': META['start'], 'end': META['end'], 'countries': META['countries'],
            'suggestions': [
                {'label': 'Explore sales', 'prompt': 'Explore sales trends', 'tool': 'sales'},
                {'label': 'Compare markets', 'prompt': 'Compare the UK and Germany', 'tool': 'markets'},
                {'label': 'Repeat customers', 'prompt': 'Understand repeat purchases and retention', 'tool': 'customers'},
                {'label': 'Explore a product', 'prompt': 'Explore a product', 'tool': 'product'},
            ]}


def completion(messages, tools=None, tool_choice='required', timeout=45):
    base = os.environ.get('RETAIL_LLM_BASE_URL', '').rstrip('/')
    if not base.startswith(('https://', 'http://127.0.0.1:', 'http://localhost:')):
        raise ProviderError('Use an HTTPS model endpoint or a local loopback endpoint.')
    payload = {'model': os.environ['RETAIL_LLM_MODEL'], 'messages': messages}
    if tools:
        payload.update({'tools': tools, 'tool_choice': tool_choice})
    headers = {'Content-Type': 'application/json'}
    key = os.environ.get('RETAIL_LLM_API_KEY')
    if key:
        headers['Authorization'] = f'Bearer {key}'
    request = urllib.request.Request(base + '/chat/completions', data=json.dumps(payload).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=max(5, timeout)) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ProviderError('The model response exceeded the permitted size.')
            value = json.loads(body)
        return value['choices'][0]['message']
    except urllib.error.HTTPError as exc:
        # Never relay provider bodies, which can contain credentials or request echoes.
        raise ProviderError(f'The configured model returned HTTP {exc.code}. Check the server-side endpoint, model and key.', exc.code) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderError('The configured model could not be reached. Check the server-side connection and retry.') from None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ProviderError('The configured endpoint did not return a compatible chat-completions response.') from None


def model_investigation(request, scope):
    # Multi-step hypothesis/evidence loop; every chart is a server computation.
    return run_agent(request, scope, completion, ProviderError)


def investigate(request):
    if not isinstance(request, dict):
        raise ValueError('Send a JSON object.')
    message = request.get('message', '')
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        raise ValueError('Enter a question of 1–4000 characters.')
    scope = validate_scope(request.get('scope'))
    for key in ['selected', 'history']:
        if key in request and (not isinstance(request[key], list) or len(request[key]) > 30 or any(not isinstance(x, dict) for x in request[key])):
            raise ValueError(f'{key} must be a list of up to 30 objects.')
    for node in request.get('selected', []):
        ev = node.get('evidence')
        if ev is not None and (not isinstance(ev, dict) or not isinstance(ev.get('scope', {}), dict)
                               or not isinstance(ev.get('definitions', []), list)):
            raise ValueError('Selected evidence must contain an object scope and a list of definitions.')
    if request.get('tool'):
        plan = guided_plan(message, scope, request.get('selected'), request.get('productCode'), request.get('countries'))
        return build_investigation(request['tool'], (plan or {}).get('scope', scope), (plan or {}).get('product_code', request.get('productCode')), (plan or {}).get('countries', request.get('countries')))
    if configured():
        return model_investigation(request, scope)
    plan = guided_plan(message, scope, request.get('selected'), request.get('productCode'), request.get('countries'))
    return build_investigation(plan['tool'], plan['scope'], plan['product_code'], plan['countries']) if plan else unsupported()
