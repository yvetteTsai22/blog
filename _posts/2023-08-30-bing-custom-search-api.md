---
date: 2023-08-30 12:05:21
layout: post
title: "Bing Custom Search API"
subtitle:
description:
image:
optimized_image:
category: blog
tags:
  - blog
author: yvetteTsai
paginate: false
---
1. add an instance in **custom bing search**
    
    [Bing Custom Search](https://www.customsearch.ai/application/2fb5152d-594b-40bd-95ee-c28d9caeceda/prod/endpoint)
    
    ![Untitled](../assets/img/2023-08-30-bing-custom-search-api/Untitled.png)
    
    ![Untitled](../assets/img/2023-08-30-bing-custom-search-api/Untitled%20(1).png)
    
    add domain to search on
    
2. register a **Bing Custom Search** in azure subscription
    
    [](https://portal.azure.com/#@TrendMicro.onmicrosoft.com/resource/subscriptions/847a5749-fae0-42df-a6f0-d943651bcbd9/resourceGroups/Workshop_2/providers/Microsoft.Bing/accounts/test_BSP/overview)
    
    ![Untitled](../assets/img/2023-08-30-bing-custom-search-api/Untitled%20(2).png)
    
3. access the azure resource
    - use this endpoint, the endpoint in the sample code is not working
        ```
        https://api.bing.microsoft.com/v7.0/custom/search?q=@{triggerBody()['text']}&customconfig=5ffcd700-1ab8-4382-8c77-32bc455916e0&mkt=en-US
        ```
        
        replace the custom config with that in **custom bing search**
        
        ![Untitled](../assets/img/2023-08-30-bing-custom-search-api/Untitled%20(3).png)
        
    - need a header
        
        Ocp-Apim-Subscription-Key: <azure bing search key>
        
        ![Untitled](../assets/img/2023-08-30-bing-custom-search-api/Untitled%20(4).png)
        
    
    sample usage in PVA
    
    [](https://web.powerva.microsoft.com/environments/Default-3e04753a-ae5b-42d4-a86d-d6f05460f9e4/bots/7648de59-d208-ee11-8f6e-00224804b843)