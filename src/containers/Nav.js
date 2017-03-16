import React, { Component } from 'react';
import AppBar from 'material-ui/AppBar';
import { Link } from 'react-router';

import DashboardIcon from 'material-ui/svg-icons/action/dashboard';
import AddCircle from 'material-ui/svg-icons/content/add-circle';
import Receipt from 'material-ui/svg-icons/action/receipt';
import Person from 'material-ui/svg-icons/social/person';
import { green700 } from 'material-ui/styles/colors';

import MenuItem from 'material-ui/MenuItem';
import Subheader from 'material-ui/Subheader';

class Nav extends Component {
    //noinspection JSMethodCanBeStatic
    render () {
        return (
            <div>
                <AppBar title="Cashfl0w" style={{background: green700}} iconStyleLeft={{display: "none"}} />
                    <Subheader>Cashfl0w</Subheader>
                    <MenuItem leftIcon={<DashboardIcon />} primaryText="Översikt" containerElement={
                        <Link to="/" />
                    } />
                    <dashboard />
                    <Subheader>Inköp</Subheader>
                    <MenuItem leftIcon={<Receipt />} primaryText="Mina inköp" containerElement={
                        <Link to="/expenses" />
                    } />
                    <MenuItem leftIcon={<AddCircle />} primaryText="Lägg till inköp" containerElement={
                        <Link to="/expenses/new" />
                    } />
                    <Subheader>Profil</Subheader>
                    <MenuItem leftIcon={<Person />} primaryText="Redigera min profil" containerElement={
                        <Link to="/profile" />
                    } />
            </div>
        );
    }
}

export default Nav;