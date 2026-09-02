import os
import json
import urllib.request
import urllib.error

import gitutils

def review_code(repo_path, provider, endpoint, model, api_key):
    try:
        if not gitutils.is_repo(repo_path):
            return {"status": "error", "message": "No es un repositorio git valido."}

        # 1. Diff del ultimo commit (via gitutils: cwd aislado + UTF-8 seguro).
        r = gitutils.run_git(repo_path, ["log", "-p", "-1"])
        if r.returncode != 0:
            return {"status": "error", "message": "No hay commits en este repositorio o no es valido."}
        diff = r.stdout or ""
        if not diff.strip():
            return {"status": "error", "message": "El diff esta vacio."}
        # Limitar tamano del diff para no saturar al modelo local.
        if len(diff) > 12000:
            diff = diff[:12000] + "\n... (diff truncado)"
            
        # 2. Preparar el Prompt
        prompt = f"""Eres un Tech Lead Senior y un experto auditor de código. Revisa el siguiente diff de git del último commit.
Detecta y reporta:
- Code Smells (malas prácticas)
- Vulnerabilidades de seguridad
- Falta de tipado o documentación
- Posibles optimizaciones

Devuelve tu respuesta formateada estrictamente en Markdown. Sé directo, constructivo y profesional. No saludes.

DIFF:
{diff}
"""
        
        # 3. Llamar a la IA
        response_text = ""
        
        if provider == "ollama":
            response_text = _call_ollama(endpoint, model, prompt)
        elif provider == "openai":
            response_text = _call_openai(endpoint, model, api_key, prompt)
        elif provider == "anthropic":
            response_text = _call_anthropic(endpoint, model, api_key, prompt)
        else:
            return {"status": "error", "message": "Proveedor de IA no soportado."}
            
        return {"status": "ok", "review": response_text}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _call_ollama(endpoint, model, prompt):
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False
    }).encode('utf-8')
    
    req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode())
            return res.get('response', "Error: No se recibió respuesta de Ollama.")
    except Exception as e:
        raise Exception(f"Fallo al conectar con Ollama en {endpoint}: {str(e)}")

def _call_openai(endpoint, model, api_key, prompt):
    if not api_key: raise Exception("Falta la API Key de OpenAI.")
    
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')
    
    req = urllib.request.Request(endpoint, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode())
            return res['choices'][0]['message']['content']
    except Exception as e:
        raise Exception(f"Fallo al conectar con OpenAI: {str(e)}")

def _call_anthropic(endpoint, model, api_key, prompt):
    if not api_key: raise Exception("Falta la API Key de Anthropic.")
    
    data = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')
    
    req = urllib.request.Request(endpoint, data=data, headers={
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode())
            return res['content'][0]['text']
    except Exception as e:
        raise Exception(f"Fallo al conectar con Anthropic: {str(e)}")


def ollama_status(endpoint):
    """Comprueba si Ollama esta corriendo. Deriva la base del endpoint
    (…/api/generate → …) y consulta /api/tags. Devuelve modelos disponibles."""
    base = endpoint or "http://localhost:11434"
    for suf in ("/api/generate", "/api/chat", "/api/tags", "/"):
        if base.endswith(suf):
            base = base[: -len(suf)]
            break
    base = base.rstrip("/")
    url = base + "/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
        return {"ok": True, "available": True, "models": models, "url": url}
    except Exception as e:
        return {"ok": True, "available": False, "error": str(e)[:160], "url": url}
