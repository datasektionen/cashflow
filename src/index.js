import React from 'react';
import ReactDOM from 'react-dom';
import { HashRouter, Route } from 'react-router-dom';
import App from './App';
import './index.css';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import {green500, green700, green100} from "material-ui/styles/colors";
import injectTapEventPlugin from 'react-tap-event-plugin';

import Expenses from './Expenses';
import Expense from './Expenses';

// Needed for onTouchTap
// http://stackoverflow.com/a/34015469/988941
injectTapEventPlugin();

const muiTheme = getMuiTheme({
    palette: {
        primary1Color: green500,
        primary2Color: green700,
        primary3Color: green100,
    },
});

const Bootstrap = () => (
    <MuiThemeProvider muiTheme={muiTheme}>
        <App />
    </MuiThemeProvider>
);

ReactDOM.render(
    <HashRouter>
        <Route exact path="/" component={Bootstrap}>
            <Route path="/expenses" component={Expenses}>
                <Route path="/expenses/:id" component={Expense} />
            </Route>
        </Route>
    </HashRouter>,
    document.getElementById('root')
);