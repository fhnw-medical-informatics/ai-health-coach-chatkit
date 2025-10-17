"""Sample widget components for the ChatKit backend."""

from __future__ import annotations

from chatkit.widgets import (
    Box,
    Card,
    Col,
    Row,
    Text,
    Title,
    WidgetComponent,
    WidgetRoot,
)


def render_sample_widget(title: str, content: str) -> WidgetRoot:
    """Build a simple sample widget."""
    
    return Card(
        key="sample",
        padding=4,
        children=[
            Col(
                gap=3,
                children=[
                    Title(
                        value=title,
                        size="lg",
                        weight="semibold",
                    ),
                    Text(
                        value=content,
                        size="sm",
                    ),
                ],
            ),
        ],
    )