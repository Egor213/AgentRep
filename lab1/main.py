from agent import Agent

if __name__ == '__main__':
    agent = Agent("team")
    try:
        agent.run(start_pos=(15, 0))
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(f"Ошибка: {e}")
        agent.stop()