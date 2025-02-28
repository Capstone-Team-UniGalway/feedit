SCRIPT_PATH="./venv/Scripts/activate"

if [ -f "$SCRIPT_PATH" ]; then
    source "$SCRIPT_PATH"
else
    echo "Virtual environment activation script not found at $SCRIPT_PATH"
fi