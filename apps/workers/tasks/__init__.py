"""
Contains background worker jobs that process asynchronously.
NOT Prefect tasks - but independent worker functions.
Run in separate worker processes, consuming jobs from queues.
"""
