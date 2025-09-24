# profile_lg_lf
profile_lg_lf (latest)

export INTENT_CLASSIFIER=llm

python run_demo.py

python -m uvicorn --app-dir /path/to/profile_aws app.server.main:app --port 9000