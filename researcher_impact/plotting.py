def set_default_fig_layout(fig, xtickvals, xticktext, ytickvals, yticktext):
    fig.add_annotation(
        text="CC BY Epoch",
        xref="paper",
        yref="paper",
        x=1.0,
        y=-0.14,
        showarrow=False,
        font=dict(
            size=12,
            color="#999999"
        ),
    )
    fig.update_layout(
        xaxis = dict(
            tickmode='array',
            tickvals=xtickvals,
            ticktext=xticktext,
        ),
        yaxis=dict(
                tickmode='array',
                tickvals=ytickvals,
                ticktext=yticktext,
        )
    )
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    fig.update_layout(
        autosize=False,
        width=800,
        height=600,
        title_x=0.5,
        margin=dict(l=100, r=30, t=80, b=80),
    )
    return fig


def save_plot(fig, folder, filename, extensions=['png', 'svg'], scale=2):
    for ext in extensions:
        fig.write_image(folder + filename + '.' + ext, scale=scale)
