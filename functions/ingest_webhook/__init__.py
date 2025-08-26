import json
import azure.functions as func

def main(req: func.HttpRequest, outQueue: func.Out[str]) -> func.HttpResponse:
    body = req.get_json()
    msg = {
        "messageId": body.get("messageId"),
        "tenant": body.get("tenant")
    }
    outQueue.set(json.dumps(msg))
    return func.HttpResponse("queued", status_code=202)
