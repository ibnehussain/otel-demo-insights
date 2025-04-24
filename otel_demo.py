# otel_demo.py (Azure-specific version)
from flask import Flask, jsonify
import logging
from random import randint
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.azuremonitor import AzureMonitorTraceExporter
from opentelemetry.exporter.azuremonitor import AzureMonitorMetricExporter

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

# B. METRICS: Set up Azure Monitor exporter
metric_provider = MeterProvider(resource=resource)
metrics.set_meter_provider(metric_provider)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter("requests.count", description="Total API requests")

# C. LOGGING (will be automatically collected by Azure)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

@app.route("/checkout", methods=["POST"])
def checkout():
    with tracer.start_as_current_span("checkout") as span:
        user_id = randint(1, 100)
        span.set_attribute("user.id", user_id)
        
        trace_id = trace.get_current_span().get_span_context().trace_id
        logger.info(f"Processing checkout for user {user_id}", extra={"trace_id": trace_id})
        
        request_counter.add(1, {"endpoint": "/checkout"})
        
        if user_id > 90:
            logger.error("Payment failed!", extra={"trace_id": trace_id})
            return jsonify({"status": "failed"}), 500
            
        return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
