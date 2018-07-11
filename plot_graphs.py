from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.plotly as py
import plotly.graph_objs as go
import argparse
import sys
import bisect
from operator import add, sub

#############################################################
# Global Plot Visual Values
chart_title_font = dict(family = 'Times New Roman',
			       size = 30,
			       color = '#7f7f7f'
		      )
title_fonts = dict(family = 'Times New Roman',
			       size = 20,
			       color = '#7f7f7f'
		      )

std_dev_up_label = 'Upper Bound Std. Dev'
std_dev_down_label = 'Lower Bound Std. Dev'

# Need to set x, name
base_line = go.Scatter(name = '',
                       line = dict(width = 3,
                                   dash = 'dash',
                                   shape = 'spline',
                                   color = 'rgb(0,0,0)'
                                   ),
                       marker = dict(opacity = 1,
                                     size = 7,
                                     line = dict(width = 1.5)
                                     ),
                       mode = 'lines+text',
                       textposition = 'top right',
                       y = []
            )

#############################################################

def isfloat(x):
    try:
        float(x)
        return True
    except:
        return False

def remove_from_all_traces(traces, exclude_vals):
    for remove in exclude_vals:
        if remove == 'STDDEV':
            for curr_trace in traces:
                for x in xrange(len(curr_trace)):
                    for this_trace_item in curr_trace:
                        if this_trace_item.name == std_dev_up_label:
                            del curr_trace[curr_trace.index(this_trace_item)]
                        elif this_trace_item.name == std_dev_down_label:
                            del curr_trace[curr_trace.index(this_trace_item)]
                        else:
                            pass
        elif remove == 'STDERR':
            for curr_trace in traces:
                for this_trace_item in curr_trace:
                    try:
                        this_trace_item.error_y = dict()
                    except AttributeError:
                        pass
        else:
            # Unrecognized value to remove
            print 'Unrecognized trace value ' + remove + ' in exclude list'



def remove_from_single_trace(trace, exclude_vals):
    for remove in exclude_vals:
        if remove == 'STDDEV':
            for x in xrange(len(trace)):
                for curr_trace in trace:
                    if curr_trace.name == std_dev_up_label:
                        del trace[trace.index(curr_trace)]
                    elif curr_trace.name == std_dev_down_label:
                        del trace[trace.index(curr_trace)]
                    else:
                        pass
        elif remove == 'STDERR':
            for curr_trace in trace:
                try:
                    curr_trace.error_y = dict()
                except AttributeError:
                    pass
        else:
            # Unrecognized value to remove
            print 'Unrecognized trace value ' + remove + ' in exclude list'


def check_to_delete(traces, delete_list, list_of_traces):
    for plot_to_remove in list_of_traces:
        if int(plot_to_remove) - 1 < len(traces):
            bisect.insort(delete_list, int(plot_to_remove) - 1)
        else:
            # Option was out of bounds of traces
            print 'DEL exclude can only be done in the proper range'


def update_graphs_with_excludes(traces, excludes):
    if excludes == None:
        # No exclusions were specified so just ignore this
        return
    graphs_del = []

    exclude_list = excludes.replace(':',' ').replace('-',' ').split()
    while len(exclude_list) != 0:
        exclude_flag = exclude_list.pop(0)
        if exclude_flag == 'ALL':
            exclude_vals = exclude_list.pop(0).split(',')
            remove_from_all_traces(traces, exclude_vals)
        elif exclude_flag.isdigit():
            if int(exclude_flag) - 1 < len(traces):
                exclude_vals = exclude_list.pop(0).split(',')
                remove_from_single_trace(traces[int(exclude_flag) - 1], exclude_vals)
            else:
                #Option was out of bounds of traces
                print 'Graph ' + exclude_flag + ' is not in graph set'
        elif exclude_flag == 'DEL':
            plots_to_remove = exclude_list.pop(0).split(',')
            check_to_delete(traces, graphs_del, plots_to_remove)
        else:
            #Unrecognized exclude
            print 'Unrecognized exclude option... Ignoring ' + exclude_val
    
    # Now we are done parsing other excludes, we can delete 
    # the traces that were specified
    if len(graphs_del) != 0:
        graphs_del = list(reversed(graphs_del))
        for graph_num in graphs_del:
            del traces[graph_num]


def create_graphs(file_name, excludes, set_base_line, y_range_max):
    fp = open(file_name, 'r')
    one_graph = False

    line = fp.readline()
    vals = line.split()
    # Checking to see all datasets are in one graph
    if vals[len(vals) - 1] == 'ALL':
        one_graph = True

    # Getting number of datasets and y_vals per dataset
    total_datasets = int(vals[0])
    poi = int(vals[1])
    line = fp.readline()
    line_split = line.split(',')
    x_title = line_split[1].replace('\n','')
    line = fp.readline()
    x_vals = [int(s) for s in line.split() if s.isdigit()]

    # List of lists
    all_trace = [[] for l in xrange(total_datasets)]
    all_layouts = []
	    
    for x in xrange(total_datasets):
        line = fp.readline()
        line_split = line.split(',')
        if line_split[0].replace('# ','') == 'line':
            all_trace[x].append(go.Scatter(x=x_vals,
                                           name=line_split[len(line_split) - 1],
                                           line = dict(width = 1,
                                                       dash = 'solid',
                                                       shape = 'spline'
                                                  ),
                                            marker = dict(opacity = 1,
                                                          size = 7,
                                                          line = dict(width = 1.5)
                                                     ),
                                            mode = 'lines+markers+text',
                                            textposition = 'bottom right'
                                            )
                               )
            all_layouts.append(go.Layout(title = '<b>' + line_split[1] + '</b>',
		                                 titlefont =  chart_title_font, 
                                         xaxis = dict(title = x_title,
		                                              titlefont = title_fonts,
                                                      autorange = False,
                                                      gridwidth = 2,
                                                      range = [0, x_vals[len(x_vals) - 1] + 2],
                                                      showgrid = True,
                                                      showline = False,
                                                      type = 'linear',
                                                      zeroline = True,
                                                      zerolinewidth = 2,
                                                      showticklabels = True,
                                                      tickcolor = 'rgb(0, 0, 0)',
                                                      ticks = 'outside',
                                                      tickvals = x_vals
                                                 ),
                                            legend = dict(x = 0.85, y = 0.05)
                                         )
                               )
        elif line_split[0].replace('# ','') == 'bar':
            all_trace[x].append(go.Bar(x=x_vals, name=line_split[len(line_split) -1],
                                       textposition = 'auto'
                                      )
                               )
            all_trace[x].append(go.Bar(x=x_vals, name=line_split[len(line_split) -1]))
            all_layouts.append(go.Layout(title='<b>' + line_split[1] + '</b>',
		                                 titlefont = chart_title_font,
                                         xaxis = dict(title = x_title,
		                                              titlefont = title_fonts,
                                                      zeroline = True,
                                                      zerolinewidth = 2,
                                                      showticklabels = True,
                                                      tickcolor = 'rgb(0, 0, 0)',
                                                      ticks = 'outside',
                                                      tickvals = x_vals
                                                 )
                                         )
                               )
        else: # bail don't know char type
            print 'Unknown plot type'
            continue
        
        for y in xrange(poi):
            line = fp.readline()
            line_split = line.split(',')
            if line_split[0].replace('# ','') == 'y-title':
                y_val_str = fp.readline()
                y_val = [float(s) for s in y_val_str.split() if isfloat(s)]
                all_layouts[x].yaxis = dict(title = line_split[1],
		                                    titlefont = title_fonts,
                                            gridwidth = 2,
                                            autorange = False,
                                            showgrid = True,
                                            showline = False,
                                            type = 'linear',
                                            zerolinewidth = 2,
                                            showticklabels = True,
                                            tickcolor = 'rgb(0, 0, 0)',
                                            ticks = 'outside'
                                            )
                for chart in all_trace[x]:
                    if line_split[len(line_split) - 1] == chart.name:
                        chart.y = y_val
            
            elif line_split[0].replace('# ','') == 'STDDEV':
                std_dev_str = fp.readline()
                std_dev = [float(s) for s in std_dev_str.split() if isfloat(s)]
                for chart in all_trace[x]:
                    if chart.type == 'bar':
                        # If this is a bar chart, we will not add standard deviations
                        break
                    if line_split[len(line_split) - 1] == chart.name:
                        all_trace[x].append(go.Scatter(name = std_dev_up_label,
			                                           y = list( map(add, chart.y, std_dev) ),
                                                       x = chart.x,
                                                       mode = 'lines',
                                                       marker = dict(color = '#444'),
                                                       line = dict(width = 0),
                                                       fillcolor = 'rgba(70, 30, 180, 0.3)',
                                                       fill = 'tonexty'
                                                       )
                                            )
                        all_trace[x].append(go.Scatter(name = std_dev_down_label,
                                                       y = list( map(sub, chart.y, std_dev) ),
                                                       x = chart.x,
                                                       mode = 'lines',
                                                       marker = dict(color = '#444'),
                                                       line = dict(width = 0),
                                                       fillcolor = 'rgba(135, 206, 250, 0.3)',
                                                       fill = 'tonexty'
                                                       )
                                            )
            elif line_split[0].replace('# ','') == 'STDERR':
                std_err_str = fp.readline()
                std_err = [float(s) for s in std_err_str.split() if isfloat(s)]
                for chart in all_trace[x]:
                    if line_split[len(line_split) - 1] == chart.name:
                        chart.error_y = dict(type = 'data',
                                             array = std_err,
                                             color = '#000',
                                             thickness = 1.5,
                                             width = 3,
                                             visible = True
                                        )
            else:
                print 'Unknown point of interest'
                continue

    # Taking care of any excludes requested
    update_graphs_with_excludes(all_trace, excludes)

    # Getting all y values from data traces, so we can just label min and
    # max below
    all_y_vals = []
    y_vals_len = 0
    for curr_trace in all_trace:
        all_y_vals.append(curr_trace[0].y)
        y_vals_len = len(curr_trace[0].y)

    # Setting all trace text labels to empty to begin with
    for curr_trace in all_trace:
        curr_trace[0].text = list(str(' ') * y_vals_len)

    # We are only going to label the min and max of the data sets
    for x in xrange(y_vals_len):
        curr_y_vals = []
        for z in xrange(len(all_y_vals)):
            curr_y_vals.append(all_y_vals[z][x])
        y_max = max(curr_y_vals)
        y_min = min(curr_y_vals)
        for curr_trace in all_trace:
            curr_trace[0].opacity
            if y_max in curr_trace[0].y:
                curr_trace[0].text[curr_trace[0].y.index(y_max)] = '<b>' + str(y_max) + '</b>'
            if y_min in curr_trace[0].y:
                curr_trace[0].text[curr_trace[0].y.index(y_min)] = '<b>' + str(y_min) + '</b>'
  
    # Creating base line trace if it was requested 
    if set_base_line != None:
        base_line_vals = set_base_line.split(',')
        print base_line_vals
        if len(base_line_vals) == 2:
            base_line.name = base_line_vals[0]
            base_line.x = all_trace[0][0].x
            for y in xrange(y_vals_len):
                base_line.y.append(float(base_line_vals[1]))
            base_line.text = list(str(' ') * y_vals_len)
            base_line.text[0] = '<b>' + base_line_vals[1] + '</b>'
        else:
            print 'Base line requires Name and Value... Not adding baseline'
    
    # Setting data range for y values
    max_y = 0
    if one_graph:
        data = []
        # Auto setting Y-Axis
        # here we need to get find max_y
        if y_range_max == None:
            for trace_x in all_trace:
                for curr_trace in trace_x:
                    data.append(curr_trace)
                    curr_max_y = max(curr_trace.y)
                    if curr_max_y > max_y:
                        max_y = curr_max_y
            all_layouts[0].yaxis.range = [0,max_y + 100] 
        else:
            for trace_x in all_trace:
                for curr_trace in trace_x:
                    data.append(curr_trace)
            all_layouts[0].yaxis.range = [0,y_range_max]
             
        # Since we are creating only one graph, we will use only one
        # layout
        layout = all_layouts[0]
        if len(data) != 0:
            # Will add baseline to plot if it was setup above
            if base_line.name != '':
                data.append(base_line)
            fig = go.Figure(data = data, layout = layout)
            plot(fig, filename='plot_all')
            #py.plot(fig, filename='plot_all')
        else:
            print 'All plots were removed, nothing to plot'
    else:
        for x in xrange(len(all_layouts)):
            max_y = 0
            data = []
            if y_range_max == None:
                for trace in all_trace[x]:
                    data.append(trace)
                    curr_max_y = max(trace.y)
                    if curr_max_y > max_y:
                        max_y = curr_max_y
                all_layouts[x].yaxis.range = [0,max_y + 100]        
            else:
                all_layouts[x].yaxis.range = [0, y_range_max]
            if len(data) != 0:
                # Will add baseline to plot if it was setup above
                if base_line.name != '':
                    data.append(base_line)
                fig = go.Figure(data = data, layout = all_layouts[x])
                plot(fig, filename='plot_' + str(x))
                #py.plot(fig, filename='plot_' + str(x))
            else:
                print 'Current plot was removed'


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                        help='Plot configuration file',
                        required=True)
    parser.add_argument('-e', '--exclude', type=str,
                        help='Values to exclude from generated plot')
    parser.add_argument('-b', '--baseline', type=str,
                        help='String and value to create baseline on plot EX: \"Device Max,5031.931\"')
    parser.add_argument('-y', '--y_range_max', type=float,
                        help='Sets the maximum value on y-axis of the plots generated')

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)
    
    try:
        fp = open(args.input_file)
        fp.close()
    except:
        print 'Invalid file passed into script...'
        exit(1)
    create_graphs(args.input_file, args.exclude, args.baseline, args.y_range_max)

if __name__ == '__main__':
    main()
