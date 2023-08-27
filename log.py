from logging import basicConfig, getLogger, INFO

basicConfig(level=INFO, format='[%(name)s] %(message)s')

logger = getLogger('anim-retarget-addon')

def info(text):
    logger.info(text)
    
def warn(text):
    logger.warn(text)