import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Router, Route, hashHistory, IndexRoute } from 'react-router';
import { Provider } from 'react-redux';

import './index.css';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import {green500, green700, green100} from "material-ui/styles/colors";
import injectTapEventPlugin from 'react-tap-event-plugin';

import App from './App';
import Dashboard from './containers/Dashboard';
import Expenses from './containers/Expenses';
import Expense from './containers/Expense';

import { loadExpenses } from './actions/ExpensesActions';

import configureStore from './store/configureStore';
const store = configureStore();

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

class Bootstrap extends Component {
    render () {
        return (
            <MuiThemeProvider muiTheme={muiTheme}>
                <App {...this.props} />
            </MuiThemeProvider>
        )
    }
}

ReactDOM.render(
    <Provider store={store}>
        <Router history={hashHistory}>
            <Route path="/" component={Bootstrap}>
                <IndexRoute component={Dashboard} />
                <Route path="expenses" component={Expenses}>
                    <Route path=":id" component={Expense} />
                </Route>
            </Route>
        </Router>
    </Provider>,
    document.getElementById('root')
);