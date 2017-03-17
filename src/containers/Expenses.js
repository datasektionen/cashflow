import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import * as ExpensesActions from '../actions/ExpensesActions';
import { connect } from "react-redux";

import Paper from 'material-ui/Paper';
import { Table, TableHeader, TableHeaderColumn, TableBody, TableRow, TableRowColumn } from 'material-ui/Table';
import {grey500} from "material-ui/styles/colors";

class Expenses extends Component {

    componentWillMount () {
        this.props.actions.loadExpenses();
        this.props.actions.setTitle("Mina inköp");
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick (arr) {
        if (arr.length === 0) {
            this.context.router.push("/expenses/");
            return;
        }

        const row = this.props.expenses[arr[0]];
        this.context.router.push("/expenses/" + row.id);
    }

    render () {
        const { expenses, children } = this.props;
        return (
            <Paper zDepth={1}>
                <div style={{padding: "5px 20px"}}>
                    <Table fixedHeader={true} fixedFooter={true} selectable={true} onRowSelection={this.handleClick}>
                        <TableHeader>
                            <TableRow>
                                <TableHeaderColumn>Beskrivning</TableHeaderColumn>
                                <TableHeaderColumn>Datum</TableHeaderColumn>
                                <TableHeaderColumn>Delar</TableHeaderColumn>
                                <TableHeaderColumn>Återbetalning</TableHeaderColumn>
                            </TableRow>
                        </TableHeader>
                        <TableBody showRowHover={true}>
                            {expenses.map(row => (
                                <TableRow key={row.id} selected={false}>
                                    <TableRowColumn>{row.description}</TableRowColumn>
                                    <TableRowColumn>{row.expense_date}</TableRowColumn>
                                    <TableRowColumn>{row.expense_parts.length} delar</TableRowColumn>
                                    <TableRowColumn>
                                        {row.reimbursement
                                            ? <div>ja</div>
                                            : <em style={{color: grey500}}>Ej utförd</em>
                                        }
                                    </TableRowColumn>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>

                    {children}
                </div>
            </Paper>
        );
    }
}

Expenses.propTypes = {
    expenses: PropTypes.array.isRequired,
    actions: PropTypes.object.isRequired
};

Expenses.contextTypes = {
    router: PropTypes.object.isRequired
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