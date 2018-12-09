import logging
import pygame


def log_time(callback, *args):
    logging.info(f'measuring time for function {callback}')
    time_before = pygame.time.get_ticks()
    result = callback(*args)
    time_after = pygame.time.get_ticks()
    time_delta = time_after - time_before
    logging.info(
        f'{callback} took {time_delta} ms')
    return result
