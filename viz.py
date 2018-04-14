import pandas as pd
from bokeh.io import output_file, save
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Legend
from bokeh.palettes import Category20_18
import re


def get_y_coordinate(x_frac, currenty, nexty, offset):
    return currenty + (nexty - currenty) * x_frac + offset


def get_coordinates(time_data, df, offset=1500):
    text_time = [float(i) for i in re.split('-| |:', time_data)]
    x_int = int(text_time[0])
    x_frac = text_time[1] / 12 + text_time[2] / 365

    currenty = df.loc[str(x_int)]['num_houses_built']
    nexty = df.loc[str(x_int + 1)]['num_houses_built']
    y = get_y_coordinate(x_frac, currenty, nexty, offset)
    return x_int + x_frac, y


def get_tweets_for_plot(tweets, df):
    x = []
    text = []
    y = []
    time = []
    for i in range(len(tweets)):
        text.append(tweets[i]['text'])
        time_data = tweets[i]['time']
        current_x, current_y = get_coordinates(time_data, df)
        x.append(current_x)
        y.append(current_y)
        time.append(time_data.split(' ')[0])
    return ColumnDataSource(dict(x=x, y=y, text=text, time=time))


def get_voting_for_plot(voting, df):
    x = []
    text = []
    y = []
    time = []
    vote = []
    for i in range(len(voting)):
        text.append(voting[i]['text'])
        vote.append(voting[i]['vote'])
        time_data = voting[i]['time']
        current_x, current_y = get_coordinates(time_data, df, offset=-1500)
        x.append(current_x)
        y.append(current_y)
        time.append(time_data.split(' ')[0])
    return ColumnDataSource(dict(x=x, y=y, text=text, time=time, vote=vote))


def plot_stats(width,
               height,
               stats_csv,
               politician_name='Stefan Löfven',
               outfile='vis.html',
               tweets=[],
               voting=[]):
    housing = pd.read_csv(stats_csv)

    sum_p = figure(
        plot_width=width,
        plot_height=height,
        title='Total amount of houses built between 1991 and 2016')

    summary_stats = housing.sum(axis=0)[2:]
    summary_stats.index.astype(int)

    summary_df = summary_stats.to_frame()
    summary_df['year'] = summary_df.index
    summary_df.columns = ['num_houses_built', 'year']

    src = ColumnDataSource(summary_df)
    line = sum_p.line(
        'year',
        'num_houses_built',
        source=src,
        legend='Housing market statistics')
    circle = sum_p.circle('year', 'num_houses_built', source=src)

    sum_hover = HoverTool(
        tooltips=[('time', '@year'), ('number of houses built',
                                      '@num_houses_built')],
        renderers=[line, circle])
    sum_p.xaxis.axis_label = 'Year'
    sum_p.yaxis.axis_label = 'Total amount of houses built'
    sum_p.add_tools(sum_hover)

    # Add tweets data
    if tweets != []:
        tweet_data = get_tweets_for_plot(dummy_tweets, summary_df)
        tweet_triangles = sum_p.inverted_triangle(
            x='x',
            y='y',
            size=15,
            color='#f48fb1',
            source=tweet_data,
            legend='Relevant tweets from ' + politician_name)
        tweet_hover = HoverTool(
            tooltips=[('time', '@time'), ('text', '@text')],
            renderers=[tweet_triangles])
        sum_p.add_tools(tweet_hover)

    # Add voting data
    if voting != []:
        voting_data = get_voting_for_plot(dummy_voting, summary_df)
        voting_triangles = sum_p.triangle(
            x='x',
            y='y',
            size=15,
            color='#80cbc4',
            source=voting_data,
            legend='Relevant votings from ' + politician_name)
        voting_hover = HoverTool(
            tooltips=[('time', '@time'), ('proposal name', '@text'), ('voting',
                                                                      'vote')],
            renderers=[voting_triangles])
        sum_p.add_tools(voting_hover)

    output_file(outfile)
    save(sum_p)


def get_dummy_data():
    dummy_tweets = [{
        'time':
        '2010-10-10 11:11:11',
        'text':
        'something useless, it\'s very useful, i promise... '
    }, {
        'time': '2015-10-10 11:11:11',
        'text': 'something useful. yeah.... yeah.... yeah.......'
    }]

    dummy_voting = [{
        'time': '2010-10-10 11:11:11',
        'text': 'voting about something',
        'vote': 'yes'
    }, {
        'time': '2015-10-10 11:11:11',
        'text': 'voting about something',
        'vote': 'no'
    }]
    return dummy_tweets, dummy_voting


dummy_tweets, dummy_voting = get_dummy_data()
plot_stats(
    800, 600, 'house-data.txt', tweets=dummy_tweets, voting=dummy_voting)
