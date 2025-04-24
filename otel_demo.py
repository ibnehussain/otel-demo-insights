from flask import Flask, jsonify
import logging
import os
from random import randint
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

# Configure resource
resource = Resource.create({"service.name": "ecommerce-api-azure"})

# A. TRACING: Set up Azure Monitor exporter
trace_provider = TracerProvider(resource=resource)
azure_trace_exporter = AzureMonitorTraceExporter.from_connection_string(
    os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)
trace_provider.add_span_processor(BatchSpanProcessor(azure_trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Flask App
app = Flask(__name__)

@app.route("/checkout", methods=["POST"])
def checkout():
    with tracer.start_as_current_span("checkout") as span:
        user_id = randint(1, 100)
        span.set_attribute("user.id", user_id)
        
        trace_id = trace.get_current_span().get_span_context().trace_id
        logging.info(f"Processing checkout for user {user_id}", extra={"trace_id": trace_id})
        
        if user_id > 90:
            logging.error("Payment failed!", extra={"trace_id": trace_id})
            return jsonify({"status": "failed"}), 500
            
        return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
