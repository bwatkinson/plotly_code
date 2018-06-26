import plotly.plotly as py
import plotly.graph_objs as go
import argparse
import sys
from operator import add, sub

#############################################################
# Global Plot Visual Values
chart_title_font = dict(family = 'Times New Roman',
			       size = 24,
			       color = '#7f7f7f'
		      )
title_fonts = dict(family = 'Times New Roman',
			       size = 24,
			       color = '#7f7f7f'
		      )

#############################################################

def isfloat(x):
    try:
        float(x)
        return True
    except:
        return False

def create_graphs(file_name):
    fp = open(file_name, 'r')

    # Getting vals
    line = fp.readline()
    vals = line.split()
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
            all_trace[x].append(go.Scatter(x=x_vals,name=line_split[len(line_split) - 1],
                                           line = dict(width = 1,
                                                       dash = 'solid',
                                                       shape = 'spline'
                                                  ),
                                           marker = dict(color = ('rgb(29, 130, 39)'),
                                                         opacity = 1,
                                                         size = 7,
                                                         line = dict(width = 1.5)
                                                    ),
                                           mode = 'lines+markers+text',
                                           text = ['pt1', 'pt2', 'pt3', 'pt4', 'pt5', 'pt6', 'pt7'],
                                           textposition = 'bottom center'
                                          )
                               )
            all_layouts.append(go.Layout(title = line_split[1],
		                                 titlefont = chart_title_font, 
                                          xaxis = dict(title = x_title,
		                                               titlefont = title_fonts,
                                                       autorange = False,
                                                       gridwidth = 2,
                                                       range = [0, x_vals[len(x_vals) - 1] + 10],
                                                       showgrid = True,
                                                       showline = False,
                                                       type = 'linear',
                                                       zeroline = True,
                                                       zerolinewidth = 2,
                                                       showticklabels = True,
                                                       tickcolor = 'rgb(0, 0, 0)',
                                                       ticks = 'outside'
                                                  )
                                         )
                               )
        elif line_split[0].replace('# ','') == 'bar':
            all_trace[x].append(go.Bar(x=x_vals, name=line_split[len(line_split) -1]))
            all_layouts.append(go.Layout(title=line_split[1],
		                                 titlefont = chart_title_font,
                                         xaxis = dict(title = x_title,
		                                              titlefont = title_fonts 
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
                                            range = [0, y_val[len(y_val) - 1] + 100],
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
                        # chart.mode = 'lines+markers+text',
                        # chart.text = [y_val],
                        # chart.textposition = 'bottom center'
            elif line_split[0].replace('# ','') == 'STDDEV':
                std_dev_str = fp.readline()
                std_dev = [float(s) for s in std_dev_str.split() if isfloat(s)]
                for chart in all_trace[x]:
                    if line_split[len(line_split) - 1] == chart.name:
                        all_trace[x].append(go.Scatter(name = 'Upper Bound Std. Dev',
			                                           y = list( map(add, chart.y, std_dev) ),
                                                       x = chart.x,
                                                       mode = 'lines',
                                                       marker = dict(color = '#444'),
                                                       line = dict(width = 0),
                                                       fillcolor = 'rgba(70, 30, 180, 0.3)',
                                                       fill = 'tonexty'
                                                       )
                                            )
                        all_trace[x].append(go.Scatter(name = 'Lower Bound Std. Dev',
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

    for x in xrange(len(all_layouts)):
        data = []
        for trace in all_trace[x]:
            data.append(trace)
        fig = go.Figure(data = data, layout = all_layouts[x])
        py.plot(fig, filename='plot_' + str(x))

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                        help='Plot configuration file',
                        required=True)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    input_file = args.input_file
    create_graphs(input_file)

if __name__ == '__main__':
    main()
