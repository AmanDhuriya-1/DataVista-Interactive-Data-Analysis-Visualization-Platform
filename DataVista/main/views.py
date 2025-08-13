import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for matplotlib

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
import matplotlib.pyplot as plt
import io
import base64
from io import StringIO  # For reading JSON safely

from .models import ContactMessage  # Import your contact model here


def home(request):
    return render(request, 'home.html')


def upload(request):
    if request.method == "POST" and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect('upload')

        try:
            df = pd.read_csv(csv_file)
            # Save dataframe to session for dashboard use (converted to JSON)
            request.session['data'] = df.to_json()
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return redirect('upload')

    return render(request, 'upload.html')


def dashboard(request):
    data_json = request.session.get('data')
    if not data_json:
        messages.error(request, "No data uploaded yet. Please upload a CSV file first.")
        return redirect('upload')

    # Load DataFrame from JSON stored in session
    df = pd.read_json(StringIO(data_json))

    # Generate summary statistics and preview HTML tables
    summary = df.describe().to_html(classes='table table-striped')
    preview = df.head().to_html(classes='table table-bordered')

    # Find numeric columns for plotting
    numeric_cols = df.select_dtypes(include=['number']).columns
    plot_url = None

    if len(numeric_cols) > 0:
        plt.style.use('dark_background')

        fig, ax = plt.subplots(figsize=(8, 4))

        # Prepare data for wave plot
        y = df[numeric_cols[0]].dropna().values
        x = range(len(y))

        # Plot line (wave style) with lime-green color
        ax.plot(x, y, color='#4ade80', linewidth=3, alpha=0.85)

        # Fill area under the wave line with translucent lime-green
        ax.fill_between(x, y, color='#22c55e', alpha=0.2)

        # Set backgrounds to match your dashboard style
        ax.set_facecolor('#1f2937')
        fig.patch.set_facecolor('#111827')

        # Grid styling
        ax.grid(True, color='#374151', linestyle='--', linewidth=0.6, alpha=0.6)

        # Titles and labels with colors matching your theme
        ax.set_title(f'Wave Plot of {numeric_cols[0]}', fontsize=16, color='#d1d5db', pad=15)
        ax.set_xlabel('Index', fontsize=13, color='#9ca3af', labelpad=10)
        ax.set_ylabel(numeric_cols[0], fontsize=13, color='#9ca3af', labelpad=10)

        # Tick label colors
        ax.tick_params(axis='x', colors='#9ca3af')
        ax.tick_params(axis='y', colors='#9ca3af')

        plt.tight_layout()

        # Save figure to bytes buffer as PNG
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        string = base64.b64encode(buf.read())
        plot_url = 'data:image/png;base64,' + string.decode('utf-8')
        plt.close()

    context = {
        'summary': summary,
        'preview': preview,
        'plot_url': plot_url,
    }
    return render(request, 'dashboard.html', context)


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if not name or not email or not message:
            messages.error(request, "Please fill in all fields.")
            return redirect('contact')

        try:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, "Thank you for your message. We'll get back to you soon!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

        return redirect('home')

    return render(request, 'contact.html')
