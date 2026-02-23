---
date: 2026-02-22 16:40:15
layout: post
title: "Level Up Your LLM Observability: A Hands-on Guide to Manual Instrumentation with Google ADK"
subtitle:
description:
image: https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2670&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D
optimized_image: >- 
 https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2670&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D
category:
tags:
    - blog
author: yvetteTsai
paginate: false
---

Large Language Models (LLMs) are rapidly transforming how we interact with technology. But with great power comes great… complexity. Understanding what’s happening inside these intricate models is crucial for performance optimization, debugging, and ensuring responsible AI practices. That’s where observability comes in.

While automated observability tools offer a quick start, sometimes you need to get your hands dirty. You need granular control over what data you collect and how you analyze it. That's where manual instrumentation shines. In this post, we'll explore how to leverage manual instrumentation with Google's ADK (Application Development Kit) to gain deeper insights into your LLM applications.

### Why Manual Instrumentation? Beyond the Black Box

Think of your LLM as a complex machine. Automated tools give you a high-level overview, like the machine's overall temperature. But what if you want to know the specific temperature of a particular component, or how frequently a certain process is being executed? That's where manual instrumentation steps in.

Manual instrumentation involves strategically adding code to your application to collect specific data points you're interested in. This provides a level of detail and customization that automated tools often can't match. Consider these benefits:

*   **Targeted Insights:** You choose exactly what data to collect, focusing on the metrics most relevant to your specific use case.
*   **Deeper Understanding:** By tracing the flow of data and events, you gain a more profound understanding of your LLM's behavior.
*   **Problem Diagnosis:** Pinpoint the root cause of issues by analyzing detailed logs and metrics.
*   **Customizable Metrics:** Create custom metrics tailored to your application's unique characteristics and needs.

Ultimately, manual instrumentation empowers you to move beyond treating your LLM as a black box and start understanding its inner workings.

### Google ADK: Your Toolkit for Observability

Google's Application Development Kit (ADK) provides a robust foundation for building observable applications. While it's designed for general application observability, it's easily adaptable for LLMs. The ADK provides libraries and tools for collecting metrics, traces, and logs, which you can then analyze using Google Cloud Observability (formerly Stackdriver).

Let’s consider how we can leverage ADK for manual instrumentation of our LLM applications.

### Hands-on Examples: Illuminating Your LLM's Behavior

Let's dive into some concrete examples of how to use manual instrumentation with ADK to improve LLM observability. We'll focus on logging and tracing.

**1. Logging Key Events:**

Logging is the cornerstone of observability. It allows you to record specific events that occur within your application, providing a historical record of its behavior.  Let's say you want to log the prompt and response of your LLM:

```python
import logging

logging.basicConfig(level=logging.INFO)

def generate_response(prompt, model):
  """Generates a response from the LLM."""
  logging.info(f"Prompt: {prompt}")
  response = model(prompt)
  logging.info(f"Response: {response}")
  return response
```

This simple example logs the prompt sent to the LLM and the response it generates. By examining these logs, you can quickly identify issues with prompt engineering or unexpected responses.

**Extending Logging:**

We can extend this further. Imagine you are working on a customer service bot. You could log not only the prompt and response, but also:

*   **User ID:** Identify the user making the request.
*   **Intent:** Log the identified intent of the user's query (e.g., "billing question", "shipping inquiry").
*   **Confidence Score:** Record the confidence score associated with the intent detection.
*   **Latency:**  Measure the time it takes for the LLM to generate a response.

By logging this information, you create a rich dataset for analyzing the bot's performance and identifying areas for improvement.

**2. Tracing Request Flow:**

Tracing allows you to track the journey of a request as it flows through your application. This is particularly useful for understanding the interactions between different components of your LLM application. Let’s look at an example where you can see how your model performs across different stages:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Configure tracing
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "my-llm-app",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})
tracer_provider = TracerProvider(resource=resource)
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

def process_user_query(query, model):
  """Processes the user query and generates a response."""
  with tracer.start_as_current_span("process_query"):
    # Extract user intent
    with tracer.start_as_current_span("extract_intent"):
      intent = extract_intent(query)

    # Generate response using LLM
    with tracer.start_as_current_span("generate_llm_response"):
      response = model(query)

    return response

def extract_intent(query):
    """Extracts the intent from the user query."""
    # Your intent extraction logic here
    return "Example Intent"
```

In this example, we use OpenTelemetry (which Google Cloud Observability supports) to create spans for the `process_query`, `extract_intent`, and `generate_llm_response` functions. This allows you to visualize the execution time of each step in the process.  By analyzing these traces, you can identify bottlenecks and optimize the performance of your application. You'll be able to see exactly how long each stage takes, from intent extraction to LLM response generation, highlighting areas that need improvement.

**Benefits of tracing for LLMs:**

*   Visualize the flow of requests through your application.
*   Identify performance bottlenecks and latency issues.
*   Understand dependencies between different components.
*   Debug complex interactions between services.

### Key Takeaways: Embrace the Power of Manual Instrumentation

Manual instrumentation offers a powerful approach to LLM observability, allowing you to gain granular insights into your application's behavior. By strategically adding logging and tracing to your code, you can collect the specific data points you need to optimize performance, debug issues, and ensure responsible AI practices.  While automated tools provide a valuable starting point, manual instrumentation empowers you to delve deeper and truly understand the inner workings of your LLM.

**Ready to get started?**

1.  **Identify your key metrics:** What are the most important aspects of your LLM's behavior that you want to track?
2.  **Start small:** Begin with simple logging statements to record key events.
3.  **Gradually introduce tracing:** Use tracing to visualize the flow of requests through your application.
4.  **Leverage Google Cloud Observability:** Analyze your logs, metrics, and traces using Google Cloud Observability to gain actionable insights.

By embracing manual instrumentation, you can unlock the full potential of your LLM applications and build more reliable, efficient, and responsible AI systems. Now go and instrument!
