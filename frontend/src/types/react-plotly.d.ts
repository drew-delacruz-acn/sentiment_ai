declare module 'react-plotly.js' {
  import * as React from 'react';
  import * as Plotly from 'plotly.js';

  interface PlotParams {
    data?: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    frames?: Plotly.Frame[];
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    className?: string;
    onInitialized?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onPurge?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onError?: (err: Error) => void;
    onBeforeHover?: () => void;
    onHover?: () => void;
    onUnhover?: () => void;
    onSelected?: () => void;
    onClick?: () => void;
    onClickAnnotation?: () => void;
    onDoubleClick?: () => void;
    onRelayout?: () => void;
    onRestyle?: () => void;
    onRedraw?: () => void;
    onAnimated?: () => void;
    onAnimatingFrame?: () => void;
    onAfterExport?: () => void;
    onAfterPlot?: () => void;
    onBeforeExport?: () => void;
    onBeforeHover?: () => void;
    useResizeHandler?: boolean;
    revision?: number;
    divId?: string;
  }

  export default class Plot extends React.Component<PlotParams> {}
} 