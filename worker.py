from application.factory import gm_worker

if __name__ == '__main__':
    try:
        print('Background job workers initialized and ready for work')
        gm_worker.work()
    except KeyboardInterrupt:
        print('Exiting')
        pass
    except Exception as e:
        print('Exiting - %s' % e)

    