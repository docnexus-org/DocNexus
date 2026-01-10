from pathlib import Path

PLUGIN_DIR = Path(__file__).parent
ENABLED_FILE = PLUGIN_DIR / "ENABLED"

def install():
    """
    'Installs' the plugin by creating the ENABLED marker file.
    In a real scenario, this could also download extra assets.
    """
    print("Activating PDF Plugin...")
    
    try:
        # Create the marker
        ENABLED_FILE.touch()
        
        # Verify xhtml2pdf availability
        try:
             import xhtml2pdf
             print("Dependency check: xhtml2pdf is available.")
        except ImportError:
             return False, "Warning: xhtml2pdf library missing from environment!"
        
        return True, "PDF Plugin Enabled Successfully."
        
    except Exception as e:
        raise RuntimeError(f"Activation failed: {e}")

if __name__ == "__main__":
    install()
