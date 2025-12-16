# Technical Tradeoffs and Design Decisions

## Language of Choice: Python

Python is a greate language for this project because it preferred for most quick tasks. It is the preferred language for AI/ML tasks due to the large ecosystem of libraries and tools available for AI and ML.

## Architecture: ETL

The architecture of this project is a simple ETL pipeline. The ETL pipeline is responsible for loading the tweets into the database, analyzing them, and then reporting on them.

### Why ETL?

1.  **Separation of Concens**: Parsing the massive and messy Twitter archive (JS file) is a distinct heavy-lifting step from the slow, logic-intensive AI analysis.
2.  **Resilience & State Recovery**: The analysis step relies on an external API (Gemini), which is subject to rate limits, network failures, and crashes. By loading data into a persistent store (SQLite) first, the worker can crash or be stopped without losing the progress of parsed tweets.
3.  **Parallelism**: Since the state is centralized in the DB, multiple workers can run in parallel (e.g., in different terminal tabs) to speed up processing without race conditions (thanks to DB locking).

## Tradeoffs 
 
1. **Hardcoded Delays**: The worker uses fixed sleep times (60s for rate limits, 30s for service unavailability) which may not align with the actual API reset headers.
2. **Uncoordinated Distributed Workers**: While multiple workers can run in parallel, they share no communication channel other than the DB. If they use the same API key, they effectively double the request rate without awareness, potentially hitting rate limits faster. Each worker maintains its own local retry counter, so one worker might be backing off while another keeps hammering the API. To co-ordinate them redis can be added to make it truly distributed.






