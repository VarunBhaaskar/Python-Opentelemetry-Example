from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import traceback
import requests
import logging
from logging.config import dictConfig
import os
from dotenv import load_dotenv

os.environ['OTEL_PYTHON_LOG_CORRELATION'] = 'true'

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.sdk.resources import Resource

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    PeriodicExportingMetricReader
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter


from AzSql import executeSqlQuery
from PSql import executePGQuery




LoggingInstrumentor().instrument(set_logging_format=True)

level = 'DEBUG'
logpath = './logs/logfile.log'

if not os.path.exists('./logs'):
    os.makedirs('./logs')
with open('./logs/logfile.log','a'):
    pass

log_format = f"""timestamp:%(asctime)s labels:{{application:AZA, env:DEV}} log.file.path:{logpath} filename:%(filename)s process.thread.name:%(threadName)s functionname:%(funcName)s \
loggername:%(name)s level:%(levelname)s errorcode:%(errorcode)s line:%(lineno)d SpanID:%(otelSpanID)s \
TraceID:%(otelTraceID)s Service:%(otelServiceName)s TraceSample:%(otelTraceSampled)s \
service.name:pythontelemtryexample service.version:1 service.type:test message:%(message)s"""

LOGGING_CONFIG = {
    'version':1 ,
    'disable_existing_loggers': False,
    'formatters': {
        'traceFormatter' : {
            'format': log_format,
            'datefmt':  '%Y-%m-%d %H:%M:%S %z'
        },
    },
    'handlers': {
        'traceLogHandler': {
            "level": level,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'traceFormatter',
            'filename': logpath,
            'when': 'midnight',
            'interval': 1,
            'backupCount': 5
        }, 
        'traceStreamHandler': {
            'level': level,
            'formatter': 'traceFormatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        }
    },
    'loggers': {
        'fastapilogger': { 
            'handlers': ['traceLogHandler','traceStreamHandler'],
            'level': 'INFO',
            'propagate': True
        }
    }
     
    }
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("fastapilogger")

try:
    load_dotenv('./.env')
except:
    logger.warning('.env file not found',extra= {'errorcode':'002'})


traceingEndpoint = os.environ.get('tracingendpoint') #otlp grpc reciever endpoint
metricsEndpoint = os.environ.get('metricsendpoint') #otlp grpc reciever endpoint
print(traceingEndpoint, metricsEndpoint)


if not traceingEndpoint:
    logger.warn('Tracing exporter endpoint not available',extra= {'errorcode':'002'})
if not metricsEndpoint:
    logger.warn('Metrics exporter endpoint not available',extra= {'errorcode':'002'})

resource = Resource(attributes={"service.name": "pythontelemtryexample","service.application":"AZA"})
tracer = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer)
tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=traceingEndpoint)))
mtracer = trace.get_tracer(__name__)
RequestsInstrumentor().instrument()

meterExporter = OTLPMetricExporter(endpoint=metricsEndpoint,)
reader = PeriodicExportingMetricReader(meterExporter)
provider = MeterProvider(metric_readers=[reader], resource=resource)
metrics.set_meter_provider(provider)


app = FastAPI(title="pythontelemtryexample")
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer, meter_provider= provider)



@app.get("/")
async def root(response: Response):
    return {"message": "Hello World from FastAPI"}

@app.get("/sql")
async def sql(response: Response):
    
    try:
        query = """select top 15 
        Title, FirstName, MiddleName,LastName, CompanyName,SalesPerson, EmailAddress, Phone
          from [SalesLT].[Customer]"""
        
        logger.info("Starting Azure SQL Query", extra={'errorcode':'000'})
        with mtracer.start_as_current_span("execute Az Sql Query"):
            result = executeSqlQuery(query)

        return {"message":result}
    except:
        logger.error(traceback.format_exc(), extra={'errorcode':'001'})
        response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return {"message":f"Exception occured. {traceback.format_exc()}"}
    
@app.get("/cosmos")
async def cosmos(response: Response):
    try:
        logger.info("starting Cosmos Query", extra={'errorcode':'000'})
        return {"message":"Cosmos DB connection not yet implemented"}
    except:
        logger.error(traceback.format_exc(), extra={'errorcode':'001'})
        response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return {"message":f"Exception occured. {traceback.format_exc()}"}

@app.get("/postgres")
async def cosmos(response: Response):
    try:
        logger.info("starting Postgres Query", extra={'errorcode':'000'})
        with mtracer.start_as_current_span("execute Postgress Query that connects to azure postgres"):
            result = executePGQuery()

        return {"message":result}
    except:
        logger.error(traceback.format_exc(), extra={'errorcode':'001'})
        response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return {"message":f"Exception occured. {traceback.format_exc()}"}
    
@app.get("/AzureFunctions")
async def cosmos(response: Response):
    functionsHelloURL = "https://rediscacheupdater.azurewebsites.net/api/SayHello"
    try:
        with mtracer.start_as_current_span("Make API call to Azure Functions API"):
            res = requests.get(functionsHelloURL)
        if res.status_code == 200:
            logger.info("Azure Functions API returned 200 status code", extra={'errorcode':'000'})
            res = res.text
            return {"message":res}
        else:
            logger.error(f"Azure Functions API returned {res.status_code} status code", extra={'errorcode':'001'})
            response.status_code = status.HTTP_417_EXPECTATION_FAILED
            return {"message": f"Azure Functions API returned {res.status_code} status code"}
    except:
        logger.error(traceback.format_exc(), extra={'errorcode':'001'})
        response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return {"message":f"Exception occured. {traceback.format_exc()}"}
    

@app.get("/news")
async def cosmos(response: Response,category:str = "entertainment"):
    newsurl = f"https://inshorts.deta.dev/news?category={category}"

    try:
        logger.info("Calling Inshorts API", extra={'errorcode':'000'})
        with mtracer.start_as_current_span("Make API call to news API"):
            res = requests.get(newsurl)
        if res.status_code == 200:
            logger.info("Inshorts API returned 200 status code", extra={'errorcode':'000'})
            res = res.json()
            return res
        else:
            logger.error(f"Inshorts API returned {res.status_code} status code")
            return {"message": f"News API returned {res.status_code} status code"}
    except:
        logger.error(traceback.format_exc(), extra={'errorcode':'001'})
        response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return {"message":f"Exception occured. {traceback.format_exc()}"}


# if __name__ == "__main__":
#    uvicorn.run("main:app", host="0.0.0.0", port=12000)

