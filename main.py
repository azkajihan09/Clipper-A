# === SUPPRESS WARNINGS ===
import os
import warnings

# Suppress TensorFlow Lite and Abseil logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging (0=all, 3=none)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations warnings
os.environ['GLOG_minloglevel'] = '2'  # Suppress Google logs (MediaPipe uses this)
os.environ['ABSL_LOG_LEVEL'] = '2'  # Suppress Abseil logs

# Suppress Python warnings (Protobuf deprecation, etc.)
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*SymbolDatabase.GetPrototype.*')

from gui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
