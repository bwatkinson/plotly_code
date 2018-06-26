import plotly.plotly as py
import plotly.graph_objs as go
import argparse
import sys
from operator import add, sub

def isfloat(x):
    try:
	float(x)
	return True
    except:
	return False


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

    fp = open(input_file, 'r')

    # Getting vals
    line = fp.readline()
    vals = line.split()
    total_datasets = int(vals[0])
    poi = int(vals[1])
    line = fp.readline()
    x_title = line.replace('# x-title ','')
    x_title = x_title.replace('\n','')
    line = fp.readline()
    x_vals = [int(s) for s in line.split() if s.isdigit()]

    # List of lists
    all_trace = [[] for l in xrange(total_datasets)]

    for x in xrange(total_datasets):
        line = fp.readline()
	# Need to change if next line will not always be chart_type and chart_title
        line_split = line.split()
        chart_type = line_split[1]
	# Chart title
	if chart_type == 'line':
	    line_split = line.replace('# line ', '')
	elif chart_type == 'bar':
	    line_split = line.replace('# bar ', '')
	chart_title = line_split
        if chart_type == 'line':
	    foo = go.Scatter(x = x_vals)
	    # Add x_vals in go.Scatter()
            all_trace[x].append(foo)
        elif chart_type == 'bar':
	    boo = go.Bar(x = x_vals)
	    # Add x_vals in go.Bar()
            all_trace[x].append(boo)
        else:
            exit(1)

        for y in xrange(poi):
            line = fp.readline()
	    line_split = line.split()
	    if line_split[1] == 'y-title':
	        y_title = line.replace('# y-title', '')
	        y_title = y_title.replace('\n', '')
		line = fp.readline()
		# This is not working because the mean values have decimals. isdigit() should be able to handle that.
		vals = [float(s) for s in line.split() if isfloat(s)]
		# Plot vals
		if chart_type == 'line':
		    # This is a new Scatter (wrong). We need to reference foo.
		    go.Scatter(y = vals)
		elif chart_type == 'bar':
		    # This is a new Bar (wrong). We need to reference foo.
		    go.Bar(y = vals)
		    # all_trace[x][0].y = vals
	    elif line_split[1] == 'STDDEV':
		# If STDDEV will be the y_title, that would go here
		line = fp.readline()
		# Get standard deviation values
		# isdigit() is not working here either
                stdev_vals = [float(s) for s in line.split() if isfloat(s)]
		if chart_type == 'bar':
		    # Ignore standard deviation
		    fp.readline()
		elif chart_type == 'line':
		    # Bounds for standard deviation
                    upper_bound = go.Scatter(
                        name = 'Upper Bound',
                        x = x_vals,
                        # y = vals + stdev_vals,
			# Element-wise addition
			y = list( map(add, vals, stdev_vals) ),
                        mode = 'lines',
                        marker = dict(color = '#444'),
                        line = dict(width = 0),
                        fillcolor = 'rgba(68, 68, 68, 0.3)',
                        fill = 'tonexty'
                    )
                    lower_bound = go.Scatter(
                        name = 'Lower Bound',
                        x = x_vals,
                        # y = vals - stdev_vals,
			# Element-wise subtraction
			y = list( map(sub, vals, stdev_vals) ),
                        mode = 'lines',
                        marker = dict(color = '#444'),
                        line = dict(width = 0)
			# Possibly add fillcolor and fill
		    )
 
	    elif line_split[1] == 'STDERR':
		# If STDERR will be the y_title, that would go here
	        line = fp.readline()
		# Get standard error values
		# isdigit() is not working here either
		err_vals = [float(s) for s in line.split() if isfloat(s)]
		if chart_type == 'line':
		    # Plot error bars
		    all_trace[x].error_y = dict(
		        type = 'data',
		        array = [err_vals],
		        visible = True
		    )
		elif chart_type == 'bar':
		    # Plot error bars
		    all_trace[x].error_y = dict(
			type = 'data',
			array = [err_vals],
			visible = True
		    )
	    # Iterate through traces
	    # Figure out len of one of the lists inside the list of lists (this should be poi)
	    data = []
	    for i in xrange(len(all_trace[x])):
		data.append(all_trace[x][y])

	    layout = go.Layout(
		title = chart_title,
		xaxis = dict(
		    title = x_title,
		    titlefont = dict(
			family = 'Courier New, monospace',
			size = 18,
			color = '#7f7f7f'
		    )
		),
		yaxis = dict(
		    title = y_title,
		    titlefont = dict(
			family = 'Courier New, monospace',
			size = 18,
			color = '#7f7f7f'
		    )
		)
	    )
	    fig = go.Figure(data = data, layout = layout)
	    # This will loop through and generate the number of plots asked for
	    py.plot(fig, filename = 'Maybe less to fix')
	# After generating plots, delete data (data = [])
	data = []

main()
