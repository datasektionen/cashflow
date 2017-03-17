import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import * as ExpenseActions from '../actions/ExpenseActions';
import { connect } from "react-redux";
import Container from 'muicss/lib/react/container';
import Row from 'muicss/lib/react/row';
import Col from 'muicss/lib/react/col';

import { Table, TableHeader, TableHeaderColumn, TableBody, TableRow, TableRowColumn } from 'material-ui/Table';
import Dialog from 'material-ui/Dialog';
import {grey500} from "material-ui/styles/colors";

class Expense extends Component {

    componentWillMount () {
        this.props.actions.loadExpense(this.props.params.id);
    }

    render () {
        const { expense } = this.props;
        return (
            <Dialog open={true} modal={true} autoScrollBodyContent={true} title={expense.description}>
                <Container fluid={true}>
                    <Row>
                        <Col sm="6">
                            <strong>Beskrivning</strong>
                        </Col>
                        <Col sm="6">
                            {expense.description}
                        </Col>
                    </Row>
                    <Row>
                        <Col sm="6">
                            <strong>Datum</strong>
                        </Col>
                        <Col sm="6">
                            {expense.expense_date}
                        </Col>
                    </Row>
                </Container>
                <h4>Delar</h4>

                <Table selectable={false}>
                        <TableHeader adjustForCheckbox={false} displaySelectAll={false}>
                            <TableRow selectable={false}>
                                <TableHeaderColumn>Nämnd</TableHeaderColumn>
                                <TableHeaderColumn>Budgetpost</TableHeaderColumn>
                                <TableHeaderColumn>Kostnadsställe</TableHeaderColumn>
                                <TableHeaderColumn>Belopp</TableHeaderColumn>
                                <TableHeaderColumn>Attestdatum</TableHeaderColumn>
                                <TableHeaderColumn>Attesterat av</TableHeaderColumn>
                            </TableRow>
                        </TableHeader>
                        <TableBody showRowHover={true} displayRowCheckbox={false}>
                            {!expense.expense_parts ? false : expense.expense_parts.map(row => (
                                <TableRow key={row.id}>
                                    <TableRowColumn>{row.budget_line.cost_centre.committee.committee_name}</TableRowColumn>
                                    <TableRowColumn>{row.budget_line.cost_centre.cost_centre_name}</TableRowColumn>
                                    <TableRowColumn>{row.budget_line.budget_line_name}</TableRowColumn>
                                    <TableRowColumn><em>{row.amount} SEK</em></TableRowColumn>
                                    <TableRowColumn>
                                        {row.attest_date
                                            ? <span>{row.attest_date}</span>
                                            : <em style={{color: grey500}}>Ej attesterad</em>
                                        }
                                    </TableRowColumn>
                                    <TableRowColumn>
                                        {row.attested_by
                                            ? <span>{row.attested_by}</span>
                                            : <em style={{color: grey500}}>Ej attesterad</em>
                                        }
                                    </TableRowColumn>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>

                {JSON.stringify(this.props.expense)}
            </Dialog>
        );
    }
}

Expense.propTypes = {
    expense: PropTypes.object.isRequired,
    actions: PropTypes.object.isRequired
};

function mapStateToProps (state) {
    return {
        expense: state.expenseReducer
    }
}

function mapDispatchToProps(dispatch) {
    return {
        actions: bindActionCreators(ExpenseActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Expense);