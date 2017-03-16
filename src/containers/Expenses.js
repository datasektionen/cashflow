import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import * as ExpensesActions from '../actions/ExpensesActions';
import { connect } from "react-redux";

class Expenses extends Component {
    render () {
        const { expenses, actions, children } = this.props;
        return (
            <div>
                <h1>Expenses</h1>

                <a onClick={actions.loadExpenses}>Fetch expenses</a>

                <ul>
                    {expenses.map(e => <li>e</li>)}
                </ul>

                <hr />
                {children}
            </div>
        );
    }
}

Expenses.propTypes = {
    expenses: PropTypes.array.isRequired
};

function mapStateToProps (state) {
    return {
        expenses: state.expenses
    }
}

function mapDispatchToProps(dispatch) {
    return {
        actions: bindActionCreators(ExpensesActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Expenses);