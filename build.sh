#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install all our Python dependencies
pip install -r requirements.txt

# 2. Run our database migrations to build the tables
flask db upgrade