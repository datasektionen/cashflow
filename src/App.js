import React, { Component, PropTypes } from 'react';
import { bindActionCreators } from "redux";
import { Link } from 'react-router';
import { connect } from "react-redux";
import * as AppActions from './actions/AppActions';

import Drawer from 'material-ui/Drawer';
import AppBar from 'material-ui/AppBar';
import Person from 'material-ui/svg-icons/social/person';
import FlatButton from 'material-ui/FlatButton';
import Snackbar from 'material-ui/Snackbar';

import Nav from './containers/Nav';

class App extends Component {
    constructor(props) {
        super(props);
        this.state = { drawerOpen: true };
        this.toggleDrawer = this.toggleDrawer.bind(this);
        props.actions.loadUser();
    }

    toggleDrawer() {
        this.setState({
            drawerOpen: !this.state.drawerOpen
        });
    }

    render() {
        const contentStyle = { transition: 'margin-left 450ms cubic-bezier(0.23, 1, 0.32, 1)' };

        if (this.state.drawerOpen)
            contentStyle.marginLeft = 256;

        const right = <FlatButton icon={<Person />} label={this.props.user.first_name} containerElement={<Link to="/profile" />} />;

        return (
            <div className="App">
                <Drawer open={this.state.drawerOpen}>
                    <Nav />
                </Drawer>

                <div style={contentStyle} className="content">
                    <AppBar title={this.props.title} onLeftIconButtonTouchTap={this.toggleDrawer} iconElementRight={right} />
                    <div style={{margin: 20}}>
                        {this.props.children}
                    </div>
                </div>

                <Snackbar message={this.props.message} open={this.props.snack} />
            </div>
        );
    }
}


App.propTypes = {
    user: PropTypes.object.isRequired,
    actions: PropTypes.object.isRequired
};

App.contextTypes = {
    store: PropTypes.object.isRequired
};

function mapStateToProps (state) {
    return {
        user: state.app.user,
        title: state.app.title,
        message: state.app.message,
        snack: state.app.snack
    }
}

function mapDispatchToProps(dispatch) {
    return {
        dispatch: dispatch,
        actions: bindActionCreators(AppActions, dispatch)
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(App);