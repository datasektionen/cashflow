import React, { Component, PropTypes } from 'react';
import Paper from 'material-ui/Paper';
import Container from 'muicss/lib/react/container';
import Row from 'muicss/lib/react/row';
import Col from 'muicss/lib/react/col';
import { SET_APP_TITLE } from '../actions/actionTypes';
import { connect } from "react-redux";

class Dashboard extends Component {
    componentWillMount () {
        this.props.setTitle();
    }

    render () {
        return (
            <Paper zDepth={1}>
                <div style={{padding: "5px 20px"}}>
                    <h1>Välkommen till Cashflow!</h1>
                    <p>
                        I cashflow kan du som är dFunktionär, eller på annat sätt engagerad inom sektionen
                        och har tillgång till en budget, lägga upp kvitton på de utlägg som du vill ha
                        återbetalning på från sektionen.
                    </p>
                    <p>
                        För att du ska kunna få återbetalning på utlägg krävs två saker:
                        <ul>
                            <li>att du har kvar och laddar upp de kvitton som det rör sig om</li>
                            <li>att du har fyllt i ett svenskt bankkontonummer under "Min profil"</li>
                        </ul>
                    </p>
                    <p>
                        Du kan ansöka om återbetalning för ett helt kvitto, eller delar av ett kvitto,
                        från en eller flera budgetposter eller kostnadsställen tillhörande någon av
                        sektionens nämnder.
                    </p>
                </div>
            </Paper>
        );
    }
}

Dashboard.propTypes = {
    setTitle: PropTypes.func.isRequired
};


function mapStateToProps () {
    return {}
}

function mapDispatchToProps(dispatch) {
    return {
        setTitle: () => dispatch({ type: SET_APP_TITLE, title: 'Översikt' })
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Dashboard);