# main.py
import signal
import threading
import time
from agent import Agent

running = True

def signal_handler(sig, frame):
    global running
    print('\nПолучен сигнал Ctrl+C')
    running = False

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    agent = Agent("team")
    agent_thread = threading.Thread(target=agent.run)
    agent_thread.start()
    
    while running:
        time.sleep(0.1)
    
    print("Останавливаем агента...")
    agent.stop()
    
    agent_thread.join(timeout=3)
    print("Программа завершена")