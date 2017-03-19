import React, {Component, PropTypes} from "react";
import {bindActionCreators} from "redux";
import * as NewExpenseActions from "../actions/NewExpenseActions";
import {connect} from "react-redux";
import request from 'superagent';

import Paper from "material-ui/Paper";
import {Table, TableHeader, TableHeaderColumn, TableBody, TableRow, TableRowColumn} from "material-ui/Table";
import DatePicker from "material-ui/DatePicker";
import Subheader from "material-ui/Subheader";
import TextField from "material-ui/TextField";
import RaisedButton from "material-ui/RaisedButton";
import MenuItem from "material-ui/MenuItem";
import SelectField from "material-ui/SelectField";
import {Stepper, Step, StepLabel, StepContent} from "material-ui/Stepper/";

import Col from "muicss/lib/react/col";
import Row from "muicss/lib/react/row";
import Container from "muicss/lib/react/container";
import Dropzone from 'react-dropzone';
import {grey500, grey600} from "material-ui/styles/colors";

class NewExpense extends Component {

    constructor (props) {
        super(props);
        this.onDrop = this.onDrop.bind(this);
    }

    componentWillMount () {
        this.props.actions.setTitle("Lägg till inköp");
        this.props.actions.loadCommittees();
    }

    render () {
        const { actions, newExpense } = this.props;
        const { data, parts, committees, costCentres, step } = newExpense;
        const { textFieldChange, loadCostCentres, constructPart } = this.props.actions;
        const style = {
            marginLeft: 20
        };
        const containerStyle = {
            marginBottom: 1
        };

        const committeeChange = (id) => {
            textFieldChange('committee', id);
            loadCostCentres(id);
        };

        return (
            <div>

                <Stepper activeStep={step} orientation="vertical">
                    <Step>
                        <StepLabel>Inköpsinformation</StepLabel>
                        <StepContent>

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
                                                hintText="Middag teambuildingevent"
                                                value={data.description}
                                                onChange={(n, d) => textFieldChange('description', d)}
                                            />
                                        </Col>
                                        <Col md="6">
                                            <DatePicker
                                                fullWidth={true}
                                                floatingLabelText="Datum"
                                                floatingLabelFixed={true}
                                                underlineShow={false}
                                                value={data.date}
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
                                        {!parts ? false : parts.map((row, index) => (
                                                <TableRow key={index}>
                                                    <TableRowColumn>{row.committee_name}</TableRowColumn>
                                                    <TableRowColumn>{row.cost_centre_name}</TableRowColumn>
                                                    <TableRowColumn>{row.budget_line_name}</TableRowColumn>
                                                    <TableRowColumn><em>{row.amount} SEK</em></TableRowColumn>
                                                </TableRow>
                                            ))}
                                    </TableBody>
                                </Table>
                            </Paper>

                            <Container fluid={true} style={style}>
                                <Row>
                                    <Col md="2">
                                        <SelectField
                                            floatingLabelText="Nämnd"
                                            fullWidth={true}
                                            value={data.committee}
                                            onChange={(e, k, v) => committeeChange(v)}>
                                            {committees.map(committee =>
                                                <MenuItem
                                                    key={committee.committee_id}
                                                    value={committee.committee_id}
                                                    primaryText={committee.committee_name} />)}
                                        </SelectField>
                                    </Col>
                                    <Col md="3">
                                        <SelectField
                                            disabled={!data.committee}
                                            floatingLabelText="Budgetpost"
                                            onChange={(e, k, v) => textFieldChange('cost_centre', v)}
                                            value={data.cost_centre}
                                            fullWidth={true}>
                                            {costCentres.map(cost_centre =>
                                                <MenuItem
                                                    key={cost_centre.cost_centre_id}
                                                    value={cost_centre.cost_centre_id}
                                                    primaryText={cost_centre.cost_centre_name} />)}
                                        </SelectField>
                                    </Col>
                                    <Col md="3">
                                        <SelectField
                                            disabled={!data.cost_centre}
                                            floatingLabelText="Kostnadsställe"
                                            onChange={(e, k, v) => textFieldChange('budget_line', v)}
                                            value={data.budget_line}
                                            fullWidth={true}>
                                            {data.cost_centre
                                                ? costCentres
                                                    .filter(cc => cc.cost_centre_id === data.cost_centre)[0]
                                                    .budget_lines
                                                    .map(bl =>
                                                        <MenuItem key={bl.budget_line_id}
                                                                  value={bl.budget_line_id}
                                                                  primaryText={bl.budget_line_name} />
                                                    ) : false
                                            }
                                        </SelectField>
                                    </Col>
                                    <Col md="2">
                                        <TextField
                                            floatingLabelText="Belopp"
                                            type="number"
                                            value={data.amount}
                                            onChange={(e, v) => textFieldChange('amount', v)}
                                            fullWidth={true} />
                                    </Col>
                                    <Col md="2">
                                        <RaisedButton
                                            style={{marginTop: 25}}
                                            label="Lägg till"
                                            disabled={!(data.committee && data.cost_centre && data.budget_line && data.amount)}
                                            onTouchTap={() => constructPart(data, committees, costCentres)}
                                        />
                                    </Col>
                                </Row>
                            </Container>

                            <div style={{marginTop: 20, marginBottom: 10}}>
                                <RaisedButton
                                    label="Spara uppgifter"
                                    primary={true}
                                    disabled={!(data.description && data.date && parts.length > 0)}
                                    onTouchTap={() => actions.submitNewExpense(newExpense)} />
                            </div>

                        </StepContent>
                    </Step>
                    <Step>
                        <StepLabel>Ladda upp kvitto</StepLabel>
                        <StepContent>
                            <Subheader>Riktlinjer</Subheader>

                            <Paper zDepth={1}>
                                <div style={{padding: "5px 20px"}}>
                                    <p>
                                        Kvitton som laddas upp får vara i bildformat (JPEG, PNG, GIF) eller PDF-format.
                                        <em> Endast av säljaren utfärdade kvitton anses vara riktiga kvitton.</em> Bankutdrag eller
                                        köpbekräftelser (markerade med "ej kvitto") är inte giltiga kvitton och går inte att
                                        få återbetalda. Köpesumman ska framgå tydligt.
                                    </p>
                                    <p>
                                        Om endast delar av ditt kvitto ska ersättas av sektionen ska du i tidigare steg
                                        ha fyllt i endast det belopp som du vill ha ersättning för. <em>Stryk över kvittorader
                                        som inte ska ersättas av sektionen utan som är personliga utgifter.</em>
                                    </p>
                                </div>
                            </Paper>

                            <Subheader>Kvittofil</Subheader>

                            <Dropzone onDrop={this.onDrop} multiple={false} style={{marginBottom: 10}}>
                                <Paper zDepth={1}>
                                   <div style={{padding: 30, textAlign: "center"}}>
                                       <em style={{color: grey500}}>Släpp en fil här, eller klicka för att välja</em>
                                   </div>
                                </Paper>
                            </Dropzone>

                        </StepContent>
                    </Step>
                    <Step>
                        <StepLabel>Klart!</StepLabel>
                        <StepContent>
                            <p>
                                Ditt inköp har sparats och kommer att behandlas av ansvarig funktionär inom kort.
                            </p>
                            <p style={{color: grey600}}>
                                Laddar du ofta upp kvitton? Kontakta Kassören eller Systemansvarig för att få tillgång
                                till Cashflows Android-app, där du kan lägga till inköp och få push-notifieringar
                                så fort din begäran uppdaterats!
                            </p>
                            <RaisedButton
                                    label="Lägg till ett nytt inköp"
                                    primary={true}
                                    style={{marginBottom: 10}}
                                    onTouchTap={actions.resetForm} />
                        </StepContent>
                    </Step>
                </Stepper>

            </div>
        );
    }

    onDrop (files) {
        const file = files[0];
        const { startUpload, failUpload, successUpload } = this.props.actions;
        startUpload();

        request.post('http://127.0.0.1:8000/api/file/')
            .field("expense", + this.props.newExpense.data.expense_id)
            .attach('file', file)
            .withCredentials()
            .end((err, res) => err ? failUpload(err) : successUpload(res));
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
        actions: bindActionCreators(NewExpenseActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(NewExpense);