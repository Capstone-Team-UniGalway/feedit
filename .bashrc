# Auto-activate venv for Feedit project
if [ -f ./venv/Scripts/activate ]; then
  echo "🟢 Auto-activating venv for Feedit"
  source ./venv/Scripts/activate
elif [ -f ./venv/bin/activate ]; then
  echo "🟢 Auto-activating venv for Feedit"
  source ./venv/bin/activate
fi