import io
import base64
import matplotlib.pyplot as plt

def get_plot_url():
    """Converts the current Matplotlib plot to a Base64 string."""
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor='#1e293b') # Match surface-slate
    img.seek(0)
    plt.close() # Close plot to free memory
    return base64.b64encode(img.getvalue()).decode('utf-8')