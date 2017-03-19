import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import * as NewExpenseActions from '../actions/NewExpenseActions';
import { connect } from "react-redux";

import Paper from 'material-ui/Paper';
import { Table, TableHeader, TableHeaderColumn, TableBody, TableRow, TableRowColumn } from 'material-ui/Table';
import DatePicker from 'material-ui/DatePicker';
import {grey500} from "material-ui/styles/colors";
import Subheader from "material-ui/Subheader";
import TextField from "material-ui/TextField";
import Divider from "material-ui/Divider";
import RaisedButton from 'material-ui/RaisedButton';
import MenuItem from 'material-ui/MenuItem';
import DropDownMenu from 'material-ui/DropDownMenu';
import SelectField from 'material-ui/SelectField';
import { Toolbar, ToolbarGroup, ToolbarTitle, ToolbarSeparator } from 'material-ui/Toolbar';

import Col from "muicss/lib/react/col";
import Row from "muicss/lib/react/row";
import Container from "muicss/lib/react/container";
import { SET_APP_TITLE } from "../actions/actionTypes";

class NewExpense extends Component {

    componentWillMount () {
        this.props.setTitle("Lägg till inköp");
    }

    render () {
        const { newExpense, actions } = this.props;
        const textFieldChange = this.props.actions.textFieldChange;
        const style = {
            marginLeft: 20
        };
        const containerStyle = {
            marginBottom: 1
        };

        return (
            <div>
                <Subheader>Inköpsdetaljer</Subheader>

                <Paper zDepth={1}>
                    <Container fluid={true} style={containerStyle}>
                        <Row>
                            <Col md="6">
                                <TextField
                                    style={style}
                                    floatingLabelText="Beskrivning"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    fullWidth={true}
                                    disabled={true}
                                    value={newExpense.description}
                                />
                            </Col>
                            <Col md="6">
                                <DatePicker
                                    fullWidth={true}
                                    floatingLabelText="Datum"
                                    floatingLabelFixed={true}
                                    underlineShow={false}
                                    value={newExpense.date}
                                    onChange={(n, d) => textFieldChange('date', d)}
                                />
                            </Col>
                        </Row>
                    </Container>
                </Paper>

                <Subheader>Kvittodelar</Subheader>

                <Paper zDepth={1}>
                    <Table selectable={false}>
                        <TableHeader adjustForCheckbox={false} displaySelectAll={false}>
                            <TableRow selectable={false}>
                                <TableHeaderColumn>Nämnd</TableHeaderColumn>
                                <TableHeaderColumn>Budgetpost</TableHeaderColumn>
                                <TableHeaderColumn>Kostnadsställe</TableHeaderColumn>
                                <TableHeaderColumn>Belopp</TableHeaderColumn>
                            </TableRow>
                        </TableHeader>
                        <TableBody displayRowCheckbox={false} stripedRows={true}>
                            {!newExpense.expense_parts ? false : newExpense.expense_parts.map(row => (
                                    <TableRow key={row.id}>
                                        <TableRowColumn>{row.budget_line.cost_centre.committee.committee_name}</TableRowColumn>
                                        <TableRowColumn>{row.budget_line.cost_centre.cost_centre_name}</TableRowColumn>
                                        <TableRowColumn>{row.budget_line.budget_line_name}</TableRowColumn>
                                        <TableRowColumn><em>{row.amount} SEK</em></TableRowColumn>
                                    </TableRow>
                                ))}
                        </TableBody>
                    </Table>
                </Paper>

                <Container fluid={true} style={style}>
                    <Row>
                        <Col md="2">
                            <SelectField floatingLabelText="Nämnd" value={2} fullWidth={true}>
                                <MenuItem value={1} primaryText="All Broadcasts" />
                                <MenuItem value={2} primaryText="All Voice" />
                                <MenuItem value={3} primaryText="All Text" />
                                <MenuItem value={4} primaryText="Complete Voice" />
                                <MenuItem value={5} primaryText="Complete Text" />
                                <MenuItem value={6} primaryText="Active Voice" />
                                <MenuItem value={7} primaryText="Active Text" />
                            </SelectField>
                        </Col>
                        <Col md="3">
                            <SelectField floatingLabelText="Budgetpost" value={2} fullWidth={true}>
                                <MenuItem value={1} primaryText="All Broadcasts" />
                                <MenuItem value={2} primaryText="All Voice" />
                                <MenuItem value={3} primaryText="All Text" />
                                <MenuItem value={4} primaryText="Complete Voice" />
                                <MenuItem value={5} primaryText="Complete Text" />
                                <MenuItem value={6} primaryText="Active Voice" />
                                <MenuItem value={7} primaryText="Active Text" />
                            </SelectField>
                        </Col>
                        <Col md="3">
                            <SelectField floatingLabelText="Kostnadsställe" value={2} fullWidth={true}>
                                <MenuItem value={1} primaryText="All Broadcasts" />
                                <MenuItem value={2} primaryText="All Voice" />
                                <MenuItem value={3} primaryText="All Text" />
                                <MenuItem value={4} primaryText="Complete Voice" />
                                <MenuItem value={5} primaryText="Complete Text" />
                                <MenuItem value={6} primaryText="Active Voice" />
                                <MenuItem value={7} primaryText="Active Text" />
                            </SelectField>
                        </Col>
                        <Col md="2">
                            <TextField floatingLabelText="Belopp" type="number" fullWidth={true} />
                        </Col>
                        <Col md="2">
                            <RaisedButton style={{marginTop: 25}} label="Lägg till" disabled={true} />
                        </Col>
                    </Row>
                </Container>

                <div style={{marginTop: 20}}>
                    <RaisedButton label="Spara uppgifter" primary={true} onTouchTap={() => actions.submitProfile(newExpense)} />
                </div>

            </div>
        );
    }
}

NewExpense.propTypes = {
    newExpense: PropTypes.object.isRequired,
    actions: PropTypes.object.isRequired
};

function mapStateToProps (state) {
    return {
        newExpense: state.newExpense
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setTitle: (title) => dispatch({ type: SET_APP_TITLE, title: title }),
        actions: bindActionCreators(NewExpenseActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(NewExpense);