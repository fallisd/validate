"""
plotter
===============

This module contains functions needed to efficiently loop
through all of the specified plots that will be produced.

.. moduleauthor:: David Fallis
"""
import os
import glob

import plotregions as pr
import defaults as dft
import plotcase as pc
import matplotlib.pyplot as plt
from yamllog import log
from copy import deepcopy

DEBUGGING = False


def single(plot):
    """ Calls the appropriate functions to output the plot
    """
    def pregion_standard(pl):
        return {'global_map': (pr.worldmap, pc.colormap),
                'section': (pr.section, pc.section),
                'polar_map': (pr.worldmap, pc.colormap),
                'polar_map_south': (pr.worldmap, pc.colormap),
                'mercator': (pr.worldmap, pc.colormap),
                }[pl]
    func_region, func_case = pregion_standard(plot['plot_projection'])
    return func_case(plot, func_region)


def compare(plot):
    """ Calls the appropriate functions to output the plot
    """
    def pregion_comp(pl):
        return {'global_map': (pr.worldmap, pc.colormap_comparison),
                'section': (pr.section, pc.section_comparison),
                'polar_map': (pr.worldmap, pc.colormap_comparison),
                'polar_map_south': (pr.worldmap, pc.colormap_comparison),
                'mercator': (pr.worldmap, pc.colormap_comparison),
                'time_series': (pr.timeseries, pc.timeseries),
                'histogram': (pr.histogram, pc.histogram),
                'zonal_mean': (pr.zonalmean, pc.zonalmean),
                'taylor': (pr.taylordiagram, pc.taylor),
                }[pl]
    func_region, func_case = pregion_comp(plot['plot_projection'])
    return func_case(plot, func_region)


def _remove_plots():
    """ Removes old plots
    """
    plots_out = []
    old_plots = glob.glob('plots/*.pdf')
    for f in old_plots:
        os.remove(f)
    old_plots = glob.glob('plots/*.png')
    for f in old_plots:
        os.remove(f)


def makeplot(p, plotnames, func):
    p['plot_type'] = func.__name__
    try:
        plot_name = func(p)
    except:
        with open('logs/log.txt', 'a') as outfile:
            outfile.write('Failed to plot ' + p['variable'] + ', ' + p['plot_projection'] + ', ' + p['data_type'] + ', ' + p['comp_model'] + '\n\n')
    else:
        p['plot_name'] = plot_name + '.pdf'
        p['png_name'] = plot_name + '.png'
        if p['pdf']:
            plotnames.append(dict(p))
            log(p)
        if p['png']:
            p['plot_name'] = p['png_name']
            log(p)
        with open('logs/log.txt', 'a') as outfile:
            outfile.write('Successfully plotted ' + p['variable'] + ', ' + p['plot_projection'] + ', ' + p['plot_type'] + ', ' + p['comp_model'] + '\n\n')


def makeplot_without_catching(p, plotnames, func):
    p['plot_type'] = func.__name__
    plot_name = func(p)
    p['plot_name'] = plot_name + '.pdf'
    p['png_name'] = plot_name + '.png'

    if p['pdf']:
        plotnames.append(dict(p))
        log(p)
    if p['png']:
        p['plot_name'] = p['png_name']
        log(p)


def calltheplot(plot, plotnames, ptype):
    funcs = {'single': single,
             'compare': compare,
             }
    if DEBUGGING:
        makeplot_without_catching(plot, plotnames, funcs[ptype])
    else:
        makeplot(plot, plotnames, funcs[ptype])


def comp_loop(plot, plotnames, ptype):
    plot['comp_flag'] = 'obs'
    for o in plot['comp_obs']:
        plot['comp_model'] = o
        plot['comp_file'] = plot['obs_file'][o]
        calltheplot(plot, plotnames, ptype)
    plot['comp_flag'] = 'cmip5'
    if plot['comp_cmips']:
        plot['comp_model'] = 'cmip5'
        plot['comp_file'] = plot['cmip5_file']
        calltheplot(plot, plotnames, ptype)
    plot['comp_flag'] = 'model'
    for model in plot['comp_models']:
        plot['comp_model'] = model
        plot['comp_file'] = plot['model_file'][model]
        calltheplot(plot, plotnames, ptype)
    plot['comp_flag'] = 'runid'
    for i in plot['id_file']:
        plot['comp_model'] = i
        plot['comp_file'] = plot['id_file'][i]
        calltheplot(plot, plotnames, ptype)


def loop_plot_types(plot, plotnames):
    if plot['plot_projection'] == 'time_series' or plot['plot_projection'] == 'zonal_mean' or plot['plot_projection'] == 'taylor' or plot['plot_projection'] == 'histogram':
        plot['comp_model'] = 'Model'
        calltheplot(plot, plotnames, 'compare')    
    else:
        plot['comp_model'] = 'Model'
        calltheplot(plot, plotnames, 'single')
        comp_loop(plot, plotnames, 'compare')

def loop(plots, debug):
    """ Loops though the list of plots and the depths within
        the plots and outputs each to a pdf

    Parameters
    ----------
    plots : list of dictionaries

    Returns
    -------
    list of tuples with (plotname, plot dictionary, plot type)
    """
    global DEBUGGING
    DEBUGGING = debug

    # Remove old plots
    _remove_plots()

    plotnames = []
    for p in plots:
        if p['depths'] == [""]:
            p['is_depth'] = False
        else:
            p['is_depth'] = True
        for d in p['depths']:
            try:
                p['depth'] = int(d)
            except: pass
            loop_plot_types(p, plotnames)
        plt.close('all')
    return plotnames


if __name__ == "__main__":
    pass
