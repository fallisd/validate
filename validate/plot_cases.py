"""
plotcase
===============

This module contains functinos for different cases of
plots. The functinos will load the appropriate data. Do
any manipulations needed for the data and direct the data
to the correct plot.

.. moduleauthor:: David Fallis
"""

import data_loader as pl
import projections as pr
import numpy as np
import scipy as sp
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib import gridspec
import defaults as dft
import datetime
from projections import default_pcolor_args


def _1d_depth_data(data, depth, plot):
    if not type(data) == 'numpy.ndarray':
        plot['plot_depth'] = None
        return data
    plot['plot_depth'] = min(depth, key=lambda x: abs(x - plot['depth']))
    try:
        depth_ind = np.where(np.round(depth) == np.round(plot['plot_depth']))[0][0]
    except:
        print('Failed to extract depth ' + plot['plot_depth'] + ' for ' + plot['variable'])
        depth_ind = 0
    data = data[depth_ind]
    return data

def _depth_data(data, depth, plot):
    """ Makes a numpy array only containing data at the desired depth

    Parameters
    ----------
    data : numpy array
    depth : numpy array
            the depth needed
    plot : dictionary

    Returns
    -------
    dictionary
    """
    if data.ndim > 2:
        plot['plot_depth'] = min(depth, key=lambda x: abs(x - plot['depth']))
        try:
            depth_ind = np.where(np.round(depth) == np.round(plot['plot_depth']))[0][0]
        except:
            print('Failed to extract depth ' + plot['plot_depth'] + ' for ' + plot['variable'])
            depth_ind = 0
        data = data[depth_ind, :, :]
    else:
        plot['plot_depth'] = None
    return data

def _full_depth_data(data, depth, plot):
    if data.ndim > 3:
        depth_ind = np.where(np.round(depth) == np.round(plot['plot_depth']))[0][0]
        data = data[:, depth_ind, :, :]
    return data


def _section_data(data, plot):
    """ Averages the data for each latitude

    Parameters
    ----------
    data : numpy array
    plot : dictionary

    Returns
    -------
    numpy array
    """
    if plot['variable'] == 'msftmyz':
        return data[plot['basin'], :, :]
    
    try:
        if data.ndim == 3:
            zonmean = data.mean(axis=2)
        elif data.ndim == 2:
            zonmean = data.mean(axis=1)
    except:
        print 'proc_plot cannot zonal mean for section ' + plot['ifile'] + ' ' + plot['variable']
        return data
    return zonmean


def _pcolor(data, plot, anom=False):
    if anom or plot['divergent']:
        anom = True    
    if not plot['data1']['pcolor_flag']:
        dpa = default_pcolor_args(data, anom)
        for key in dpa:
            plot['data1']['pcolor_args'][key] = dpa[key]

def _comp_pcolor(data, obs, plot, anom=False):
    """ Gives the data and observations the same colorbar
        for comparison

    Parameters
    ----------
    data : numpy array
    obs : numpy array
    plot : dictionary
    ptype : string
            'climatology' or 'trends'
    """
    if anom or plot['divergent']:
        anom = True  
    if not plot['data1']['pcolor_flag'] and not plot['data2']['pcolor_flag']:
        d1pca = default_pcolor_args(data, anom)
        d2pca = default_pcolor_args(obs, anom)

        vmin = np.min([d1pca['vmin'], d2pca['vmin']])
        vmax = np.max([d1pca['vmax'], d2pca['vmax']])

        d1pca['vmin'] = vmin
        d1pca['vmax'] = vmax
        for key in d1pca:
            plot['data1']['pcolor_args'][key] = d1pca[key]
        for key in d1pca:
            plot['data2']['pcolor_args'][key] = d1pca[key]        


def savefigures(plotname, png=False, pdf=False, **kwargs):
    pdfname = plotname + '.pdf'
    pngname = plotname + '.png'
    if png:
        plt.savefig(pngname, bbox_inches='tight')
    if pdf:
        plt.savefig(pdfname, bbox_inches='tight')

def plotname(plot):
    plotname = 'plots/'
    plotname += plot['variable']
    plotname += plot['data_type']
    plotname += '_' + plot['plot_projection']
    plotname += '_' + str(plot['plot_depth'])
    plotname += '_' + plot['dates']['start_date'] + plot['dates']['end_date']
    season = ''.join(plot['seasons'])
    plotname += season

    try: 
        plotname += '_' + str(plot['basin'])
    except:
        pass
    
    if plot['comp_flag'] == 'Model' or not plot['comp_flag']:
        return plotname
    try:
        plotname += '_' + plot['comp_model']
    except: pass
    plotname += '_' + plot['comp_dates']['start_date'] + plot['comp_dates']['end_date']
    compseason = ''.join(plot['comp_seasons'])
    plotname += compseason

    print plotname
    return plotname    
        

def colormap(plot):
    """ Loads and plots the data for a time averaged map

    Parameters
    ----------
    plot : dictionary
    func : a method that will plot the data on a specified map

    Returns
    -------
    string : name of the plot
    """
    print 'plotting map of ' + plot['variable']
    # load data from netcdf file
    data, lon, lat, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                          plot['dates'], realm=plot['realm_cat'], 
                                          scale=plot['scale'], shift=plot['shift'], 
                                          remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                          seasons=plot['seasons'], datatype=plot['data_type'],
                                          cdostring=plot['cdostring'])
    if plot['data_type'] == 'trends':
        data, units = _trend_units(data, units, plot)
    if plot['units']:
        units = plot['units']
    # get data at correct depth
    data = _depth_data(data, depth, plot)
    
    if plot['sigma'] and plot['data_type'] == 'trends':
        detrenddata, _, _, _, _, _ = pl.dataload(plot['ifile'], plot['variable'],
                                         plot['dates'], realm=plot['realm_cat'],
                                         scale=plot['scale'], shift=plot['shift'],
                                         remapf=plot['remap'], remapgrid=plot['remap_grid'],
                                         seasons=plot['seasons'], datatype='detrend')
        detrenddata = _full_depth_data(detrenddata, depth, plot)
        siggrid = trend_significance(detrenddata, plot['sigma'])
        cvalues, _ = _trend_units(siggrid, units, plot)
    else:
        cvalues = None 

    dft.filltitle(plot)

    anom = True if plot['divergent'] or plot['data_type'] == 'trends' else False

    _pcolor(data, plot, anom=anom)
    # make plot
    pr.worldmap(plot['plot_projection'], lon, lat, data, ax_args=plot['data1']['ax_args'],
         pcolor_args=plot['data1']['pcolor_args'], cblabel=units, plot=plot, cvalues=cvalues,
         **plot['plot_args'])

    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    plot['units'] = units
    return plot_name

def ttest(data1, data2):
    t, p = sp.stats.ttest_ind(data1, data2, axis=0, equal_var=False)
    return p

def colormap_comparison(plot):
    """ Loads and plots the data for a time averaged map.
        Loads and plots the data for comparison and plots the
        difference between the data and the comparison data.

    Parameters
    ----------
    plot : dictionary
    func : a method that will plot the data on a specified map

    Returns
    -------
    string : name of the plot
    """
    print 'plotting comparison map of ' + plot['variable']
    # load data from netcdf file
    data, lon, lat, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                          plot['dates'], realm=plot['realm_cat'], 
                                          scale=plot['scale'], shift=plot['shift'], 
                                          remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                          seasons=plot['seasons'], datatype=plot['data_type'],
                                          cdostring=plot['cdostring'])
    data = _depth_data(data, depth, plot)
    
    data2, _, _, _, _, _ = pl.dataload(plot['comp_file'], plot['variable'], 
                                        plot['comp_dates'], realm=plot['realm_cat'], 
                                        scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['comp_seasons'], datatype=plot['data_type'],
                                        cdostring=plot['cdostring'],
                                        depthneeded=[plot['plot_depth']])
    data2 = _depth_data(data2, depth, plot)
    
    if plot['data_type'] == 'trends':
        data, units = _trend_units(data, units, plot)
        data2, _ = _trend_units(data2, units, plot)
    if plot['units']:
        units = plot['units']
    # get data at correct depth

    if plot['alpha'] and plot['data_type'] == 'climatology':
        fulldata, _, _, _, _, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                      plot['dates'], realm=plot['realm_cat'], 
                                      scale=plot['scale'], shift=plot['shift'], 
                                      remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                      seasons=plot['seasons'], depthneeded=[plot['plot_depth']])
        fulldata2, _, _, _, _, _, = pl.dataload(plot['comp_file'], plot['variable'], 
                                        plot['comp_dates'], realm=plot['realm_cat'], 
                                        scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['comp_seasons'], depthneeded=[plot['plot_depth']])
        pvalues = ttest(fulldata, fulldata2)
    else:
        pvalues = None
    
    if plot['sigma'] and plot['data_type'] == 'trends':
        detrenddata, _, _, _, _, _ = pl.dataload(plot['ifile'], plot['variable'],
                                         plot['dates'], realm=plot['realm_cat'],
                                         scale=plot['scale'], shift=plot['shift'],
                                         remapf=plot['remap'], remapgrid=plot['remap_grid'],
                                         seasons=plot['seasons'], datatype='detrend')
        detrenddata = _full_depth_data(detrenddata, depth, plot)
        siggrid = trend_significance(detrenddata, plot['sigma'])
        cvalues, _ = _trend_units(siggrid, units, plot)
        detrenddata, _, _, _, _, _ = pl.dataload(plot['comp_file'], plot['variable'],
                                         plot['comp_dates'], realm=plot['realm_cat'],
                                         scale=plot['comp_scale'], shift=plot['comp_shift'],
                                         remapf=plot['remap'], remapgrid=plot['remap_grid'],
                                         seasons=plot['comp_seasons'], datatype='detrend')
        detrenddata = _full_depth_data(detrenddata, depth, plot)
        siggrid = trend_significance(detrenddata, plot['sigma'])
        c2values, _ = _trend_units(siggrid, units, plot)        
    else:
        cvalues = None 
        c2values = None

    try:
        compdata = data - data2
    except:
        data2 = data2.transpose()
        compdata = data - data2
    anom = True if plot['divergent'] or plot['data_type'] == 'trends' else False
    _comp_pcolor(data, data2, plot)

    dft.filltitle(plot)
    fig, (axl, axm, axr) = plt.subplots(3, 1, figsize=(8, 8))


    # make plots of data, comparison data, data - comparison data
    pr.worldmap(plot['plot_projection'], lon, lat, data, plot=plot, ax=axl, ax_args=plot['data1']['ax_args'],
         pcolor_args=plot['data1']['pcolor_args'], cblabel=units, cvalues=cvalues,
         **plot['plot_args'])
    pr.worldmap(plot['plot_projection'], lon, lat, data2, plot=plot, ax=axm, ax_args=plot['data2']['ax_args'],
         pcolor_args=plot['data2']['pcolor_args'], cblabel=units, cvalues=c2values,
         **plot['plot_args'])
    pr.worldmap(plot['plot_projection'], lon, lat, compdata, pvalues=pvalues, alpha=plot['alpha'], anom=True, 
         rmse=True, plot=plot, ax=axr, ax_args=plot['comp']['ax_args'],
         pcolor_args=plot['comp']['pcolor_args'], cblabel=units, **plot['plot_args'])
    
    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    plot['units'] = units
    return plot_name


def section(plot):
    """ Loads and plots the data for a time average section map.

    Parameters
    ----------
    plot : dictionary
    func : a method that will plot the data on a specified map

    Returns
    -------
    string : name of the plot
    """
    print 'plotting section of ' + plot['variable']
    
    data, _, lat, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                        plot['dates'], realm=plot['realm_cat'], 
                                        scale=plot['scale'], shift=plot['shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['seasons'], datatype=plot['data_type'],
                                        section=True, cdostring=plot['cdostring'])

    if plot['data_type'] == 'trends':
        data, units = _trend_units(data, units, plot)
    if plot['units']:
        units = plot['units']

    dft.filltitle(plot)
    anom = True if plot['divergent'] or plot['data_type'] == 'trends' else False
    _pcolor(data, plot, anom=anom)

    fig = plt.figure(figsize=(10,3))
    gs = gridspec.GridSpec(1, 1, width_ratios=[1, 1])    
    # plot the data
    pr.section(lat, depth, data, plot=plot, ax=plt.subplot(gs[0, 0]), ax_args=plot['data1']['ax_args'],
         pcolor_args=plot['data1']['pcolor_args'], cblabel=units)
    
    plot_name = plotname(plot)

    savefigures(plot_name, **plot)
    plot['units'] = units
    return plot_name


def section_comparison(plot):
    """ Loads and plots the data for a time averaged section map.
        Loads and plots the data for comparison and plots the
        difference between the data and the comparison data.

    Parameters
    ----------
    plot : dictionary
    func : a method that will plot the data on a specified map

    Returns
    -------
    string : name of the plot
    """
    print 'plotting section comparison of ' + plot['variable']
    data2, _, _, depth, _, _ = pl.dataload(plot['comp_file'], plot['variable'], 
                                        plot['comp_dates'], realm=plot['realm_cat'], 
                                        scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['comp_seasons'], datatype=plot['data_type'],
                                        section=True, cdostring=plot['cdostring'])
    print depth.shape
    data, _, lat, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                        plot['dates'], realm=plot['realm_cat'], 
                                        scale=plot['scale'], shift=plot['shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['seasons'], datatype=plot['data_type'],
                                        section=True, cdostring=plot['cdostring'], 
                                        depthneeded=list(depth))

    if plot['data_type'] == 'trends':
        data, units = _trend_units(data, units, plot)
        data2, _ = _trend_units(data2, units, plot)
    if plot['units']:
        units = plot['units']
        
    compdata = data - data2
    dft.filltitle(plot)
    anom = True if plot['divergent'] or plot['data_type'] == 'trends' else False
    _comp_pcolor(data, data2, plot, anom=anom)

    if plot['alpha'] and plot['data_type'] == 'climatology':
        fulldata, _, _, _, _, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                      plot['dates'], realm=plot['realm_cat'], 
                                      scale=plot['scale'], shift=plot['shift'], 
                                      remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                      seasons=plot['seasons'], depthneeded=list(depth),
                                      section=True)
        fulldata2, _, _, _, _, _, = pl.dataload(plot['comp_file'], plot['variable'], 
                                        plot['comp_dates'], realm=plot['realm_cat'], 
                                        scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['comp_seasons'], depthneeded=list(depth),
                                        section=True)
        pvalues = ttest(fulldata, fulldata2)
    else:
        pvalues = None

    
    # make plots of data, comparison data, data - comparison data
    fig = plt.figure(figsize=(6, 8))
    gs = gridspec.GridSpec(3, 2, width_ratios=[20, 1])
    pr.section(lat, depth, data, plot=plot, ax=plt.subplot(gs[0, 0]), ax_args=plot['data1']['ax_args'],
         pcolor_args=plot['data1']['pcolor_args'], cblabel=units, cbaxis=plt.subplot(gs[0, 1]))
    pr.section(lat, depth, data2, plot=plot, ax=plt.subplot(gs[1, 0]), ax_args=plot['data2']['ax_args'],
         pcolor_args=plot['data2']['pcolor_args'], cblabel=units, cbaxis=plt.subplot(gs[1, 1]))
    pr.section(lat, depth, compdata, anom=True, rmse=True, pvalues=pvalues, 
         alpha=plot['alpha'], plot=plot, ax=plt.subplot(gs[2, 0]), ax_args=plot['comp']['ax_args'],
         pcolor_args=plot['comp']['pcolor_args'], cblabel=units, cbaxis=plt.subplot(gs[2, 1]))

    plt.tight_layout()
    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    plot['units'] = units
    return plot_name


def _trend_units(data, units, plot):
    """ Multiplies the data by a scalar factor based on the frequency

    Parameters
    ----------
    data : numpy array
    units : string
    plot : dictionary

    Returns
    -------
    numpy array
    string
    """
    if plot['frequency'] == 'day':
        data = data * 3650
        data = data * len(plot['seasons']) / 4
    if plot['frequency'] == 'mon':
        data = data * 120
        data = data * len(plot['seasons']) / 4
    if plot['frequency'] == 'year':
        data = data * 10
    units = units + '/decade'
    return data, units

def trend_significance(residuals, sigma=0.05):
    nt = len(residuals)
    count = 0
    x = len(residuals[0, :, 0])
    y = len(residuals[0, 0, :])
    rcorrs = np.empty(shape=[x, y])
    for (i,j), value in np.ndenumerate(rcorrs):
        count += 1
        r_corr,_ = sp.stats.pearsonr(residuals[: -1, i, j], residuals[1:, i, j])
        if r_corr < 0:
            r_corr = 0
        rcorrs[i][j] = r_corr
    
    cs = np.empty(shape=[x, y])    
    for (i,j), rcor in np.ndenumerate(rcorrs):
        neff = float(nt * (1-rcor) / (1 + rcor))
        #neff = nt
        a = residuals[:,i,j]
        b = a * a
        d = sum(b)
        se = np.sqrt( d / ( neff - 2 ) )
        sb = se / np.sqrt( sum( ( np.arange(nt) - np.mean( np.arange(nt) ) )**2 ) )

        tcrit = sp.stats.t.isf(sigma/2.0, nt - 2 )

        c = tcrit * sb

        cs[i][j] = c
    return cs

def _histogram_data(plot, compfile):
    data, _, _, _, _, _ = pl.dataload(compfile, plot['variable'], 
                              plot['comp_dates'], realm=plot['realm_cat'], 
                              scale=plot['comp_scale'], shift=plot['comp_shift'], 
                              remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                              seasons=plot['comp_seasons'], datatype=plot['data_type'],
                              fieldmean=True, cdostring=plot['cdostring'],
                              depthneeded=plot['plot_depth'])
    data, _ = _trend_units(data, '', plot)
    return data

def histogram(plot):
    values = {}
    data, _, _, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                              plot['comp_dates'], realm=plot['realm_cat'], 
                              scale=plot['comp_scale'], shift=plot['comp_shift'], 
                              remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                              seasons=plot['comp_seasons'], datatype=plot['data_type'],
                              cdostring=plot['cdostring'], fieldmean=True)
    
    data = _1d_depth_data(data, depth, plot)
    data, units = _trend_units(data, units, plot)
    
    if plot['units']:
        units = plot['units']

    values[plot['model_ID']] = data

    for o in plot['comp_obs']:
        values[o] = _histogram_data(plot, plot['obs_file'][o])

    for i in plot['comp_ids']:
        values[i] = _histogram_data(plot, plot['id_file'][i])

    for m in plot['comp_models']:  
        values[m] = _histogram_data(plot, plot['model_file'][m])

    cmipdata = []
    for f in plot['cmip5_files']:
        cmipdata.append(_histogram_data(plot, f))
    
    
    dft.filltitle(plot)
    plot['data1']['ax_args']['xlabel'] = 'Trends ' + plot['comp_dates']['start_date'][:4] + '-' + plot['comp_dates']['end_date'][:4] + ' (' + units + ')'
    plot['data1']['ax_args']['ylabel'] = '# Realizations'
    pr.histogram(cmipdata, values, ax_args=plot['data1']['ax_args'], plot=plot)
    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    plot['units'] = units
    return plot_name
    
def _timeseries_data(plot, compfile):
    data, _, _, _, _, time = pl.dataload(compfile, plot['variable'], 
                                         plot['comp_dates'], realm=plot['realm_cat'], 
                                         scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                         remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                         seasons=plot['comp_seasons'], fieldmean=True,
                                         cdostring=plot['cdostring'],
                                         depthneeded=[plot['plot_depth']])

    return data, time


def timeseries(plot):
    print 'plotting timeseries comparison of ' + plot['variable']

    data, _, _, depth, units, time = pl.dataload(plot['ifile'], plot['variable'], 
                                         plot['dates'], realm=plot['realm_cat'], 
                                         scale=plot['scale'], shift=plot['shift'], 
                                         remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                         seasons=plot['seasons'], fieldmean=True,
                                         cdostring=plot['cdostring'])
    
    plot['data1']['ax_args']['xlabel'] = 'Time'
    if 'ylabel' not in plot['data1']['ax_args']:
        if plot['units']:
            plot['data1']['ax_args']['ylabel'] = plot['units']
        else:
            plot['data1']['ax_args']['ylabel'] = units
            plot['units'] = units
    plot['plot_depth'] = None
    if data.ndim > 1:
        plot['plot_depth'] = min(depth, key=lambda x: abs(x - plot['depth']))

        try:
            depth_ind = np.where(np.round(depth) == plot['plot_depth'])[0][0]
        except:
            print('Failed to extract depth ' + plot['plot_depth'] + ' for ' + plot['variable'])
            depth_ind = 0
        data = data[:, depth_ind]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    dft.filltitle(plot)
    
    # make plot
    pr.timeseries(time, data, plot=plot, ax=ax, label=plot['model_ID'], ax_args=plot['data1']['ax_args'], color='r', zorder=6)
    handles = [mpatches.Patch(color='r', label=plot['model_ID'])]

    # plot comparison data on the same axis
    if plot['cmip5_file']:
        plot['comp_model'] = 'cmip5'
        data, x = _timeseries_data(plot, plot['cmip5_file'])
        pr.timeseries(x, data, plot=plot, ax=ax, label=plot['comp_model'], ax_args=plot['data1']['ax_args'], color='k', zorder=4)
        handles.append(mpatches.Patch(color='k', label=str(plot['comp_model'])))
    for o in plot['comp_obs']:
        plot['comp_model'] = o
        data, x = _timeseries_data(plot, plot['obs_file'][o])
        pr.timeseries(x, data, plot=plot, ax=ax, label=plot['comp_model'], ax_args=plot['data1']['ax_args'], color='b', zorder=5)
        handles.append(mpatches.Patch(color='b', label=str(plot['comp_model'])))
    for model in plot['comp_models']:
        plot['comp_model'] = model
        data, x = _timeseries_data(plot, plot['model_file'][model])
        pr.timeseries(x, data, plot=plot, ax=ax, label=plot['comp_model'], ax_args=plot['data1']['ax_args'], color='g', zorder=2)
        handles.append(mpatches.Patch(color='g', label=str(plot['comp_model'])))
    for i in plot['comp_ids']:
        plot['comp_model'] = i
        data, x = timeseriesdata(plot, plot['id_file'][i], depth)
        pr.timeseries(x, data, plot=plot, ax=ax, label=plot['comp_model'], ax_args=plot['data1']['ax_args'], color='y', zorder=3)
        handles.append(mpatches.Patch(color='y', label=str(plot['comp_model'])))

    for f in plot['cmip5_files']:
        try:
            plot['comp_model'] = 'cmip'
            data, x = _timeseries_data(plot, f)
            pr.timeseries(x, data, plot=plot, ax=ax, label=None, ax_args=plot['data1']['ax_args'], color='0.75', zorder=1)
        except:
            continue

    ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1, 0.5))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))
    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    return plot_name

def zonalmeandata(plot, compfile):

    data, _, _, _, _, _ = pl.dataload(compfile, plot['variable'], 
                                  plot['comp_dates'], realm=plot['realm_cat'], 
                                  scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                  remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                  seasons=plot['comp_seasons'], datatype=plot['data_type'],
                                  section=True, depthneeded=[plot['plot_depth']])

    return data

def zonalmean(plot):
    """ Loads and plots a time average of the zonal means
        for each latitude. Loads and plots the data for comparison.

    Parameters
    ----------
    plot : dictionary
    func : a method that will plot the data on a specified map

    Returns
    -------
    string : name of the plot
    """
    print 'plotting zonal mean of ' + plot['variable']
    data, _, lat, depth, units, _ = pl.dataload(plot['ifile'], plot['variable'], 
                                        plot['dates'], realm=plot['realm_cat'], 
                                        scale=plot['scale'], shift=plot['shift'], 
                                        remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                        seasons=plot['seasons'], datatype=plot['data_type'],
                                        section=True)

    plot['data1']['ax_args']['xlabel'] = 'Latitude'
    if 'ylabel' not in plot['data1']['ax_args']:
        if plot['units']:
            plot['data1']['ax_args']['ylabel'] = plot['units']
        else:
            plot['data1']['ax_args']['ylabel'] = units
            plot['units'] = units
    # get data at the correct depth 
    plot['plot_depth'] = None
    if data.ndim > 1:
        plot['plot_depth'] = min(depth, key=lambda x: abs(x - plot['depth']))
        try:
            depth_ind = np.where(np.round(depth) == plot['plot_depth'])[0][0]
        except:
            print('Failed to extract depth ' + plot['plot_depth'] + ' for ' + plot['variable'])
            depth_ind = 0
        data = data[depth_ind, :]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    dft.filltitle(plot)
   
    # make plot
    pr.zonalmean(lat, data, plot=plot, ax=ax, ax_args=plot['data1']['ax_args'], color='r', zorder=6)
    handles = [mpatches.Patch(color='r', label=plot['model_ID'])] 
    
    # plot comparison data on the same axis
    if plot['comp_cmips']:
        plot['comp_model'] = 'cmip5'
        data = zonalmeandata(plot, plot['cmip5_file'])
        pr.zonalmean(lat, data, plot=plot, ax=ax, label=plot['comp_model'], color='k', zorder=4)
        handles.append(mpatches.Patch(color='k', label='cmip5')) 
    for o in plot['comp_obs']:
        plot['comp_model'] = o
        data = zonalmeandata(plot, plot['obs_file'][o])
        pr.zonalmean(lat, data, plot=plot, ax=ax, label=plot['comp_model'], color='b', zorder=5)
        handles.append(mpatches.Patch(color='b', label=str(plot['comp_model'])))
    for m in plot['comp_models']:
        plot['comp_model'] = model
        data = zonalmeandata(plot, plot['model_file'][m])
        pr.zonalmean(lat, data, plot=plot, ax=ax, label=plot['comp_model'], color='g', zorder=2)        
        handles.append(mpatches.Patch(color='g', label=str(plot['comp_model'])))
    for i in plot['comp_ids']:
        plot['comp_model'] = i
        data = zonalmeandata(plot, plot['id_file'][i])
        pr.zonalmean(lat, data, plot=plot, ax=ax, label=plot['comp_model'], color='y', zorder=3)
        handles.append(mpatches.Patch(color='y', label=str(plot['comp_model'])))

    for f in plot['cmip5_files']:
        plot['comp_model'] = 'cmip'
        data = zonalmeandata(plot, f)
        pr.zonalmean(lat, data, plot=plot, ax=ax, color='0.75', zorder=1)

    ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1, 0.5))
    plot_name = plotname(plot)
    savefigures(plot_name, **plot)
    return plot_name


def taylordata(plot, compfile, depthneeded):
    data, _, _, _, _, _, = pl.dataload(compfile, plot['variable'], 
                                      plot['comp_dates'], realm=plot['realm_cat'], 
                                      scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                      remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                      seasons=plot['comp_seasons'], datatype=plot['data_type'],
                                      depthneeded=depthneeded)
    return data

def taylor(plot):
    print 'plotting taylor diagram of ' + plot['variable']
    for o in plot['obs_file']:
        refdata, _, _, depth, units, _ = pl.dataload(plot['obs_file'][o], plot['variable'], 
                                             plot['comp_dates'], realm=plot['realm_cat'], 
                                             scale=plot['comp_scale'], shift=plot['comp_shift'], 
                                             remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                             seasons=plot['comp_seasons'], datatype=plot['data_type']) 
        break
    data, _, _, _, _, _, = pl.dataload(plot['ifile'], plot['variable'], 
                                  plot['dates'], realm=plot['realm_cat'], 
                                  scale=plot['scale'], shift=plot['shift'], 
                                  remapf=plot['remap'], remapgrid=plot['remap_grid'], 
                                  seasons=plot['comp_seasons'], datatype=plot['data_type'],
                                  depthneeded=list(depth))
    labelled_data = [(data, plot['model_ID'], 'r')]
    unlabelled_data = []
    dft.filltitle(plot)

    for f in plot['cmip5_files']:
        plot['comp_model'] = f
        try:
            data = taylordata(plot, f, depth)
            unlabelled_data.append((data, f))
        except:
            continue
    # get data from models and cmip and append to plotdata list
    if plot['cmip5_file']:
        plot['comp_model'] = 'cmip5'
        try:
            data = taylordata(plot, plot['cmip5_file'], depth)
            labelled_data.append((data, 'cmip5', 'k'))
        except:
            pass
    for model in plot['comp_models']:
        plot['comp_model'] = model
        try:
            data = taylordata(plot, plot['model_file'][model], depth)
            plotdata.append((data, model, 'b'))
        except:
            continue
    for i in plot['comp_ids']:
        plot['comp_model'] = i
        try:
            data = taylordata(plot, plot['id_file'][i], depth)
            plotdata.append((data, i, 'g'))
        except:
            continue
    
    # make plot
    pr.taylordiagram(refdata, labelled_data, unlabelled_data, plot=plot, ax_args=plot['data1']['ax_args'])
    
    plot_name = plotname(plot)
    plt.tight_layout()
    savefigures(plot_name, **plot)
    if not plot['units']:
        plot['units'] = units
    plot['comp_file'] = plot['obs_file']
    return plot_name
    
    plot_name = plotname(plot)
    plt.tight_layout()
    savefigures(plot_name, **plot)
    if not plot['units']:
        plot['units'] = units
    plot['comp_file'] = plot['obs_file']
    return plot_name
 
