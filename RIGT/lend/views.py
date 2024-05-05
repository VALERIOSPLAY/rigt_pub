from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
import os
import threading
import subprocess
def index_page(request):


    # Создание и запуск потока
    thread = threading.Thread(target=run_script)
    thread.start()

    print('run bot')
    return render(request, 'index.html')

def run_script():
    # Запуск вашего скрипта
    subprocess.call(["python", "bot_main.py"])