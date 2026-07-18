# Django applications

Cashflow is split into several Django applications that are responsible for different parts of the system.

## Cashflow

As per Django convention we have a `cashflow` application (this is the nested `cashflow` directory, not the root
directory). This app contains the management script `manage.py`, application config (`settings.py`) and
the root URL configuration (`urls.py`). It also contains functionality specific to the Computer Science Chapter's other
systems, for example our budget system GOrdian and profile picture service.

## Core

_TODO — shared, organization-agnostic API building blocks (serializers, filters, pagination) used by 2+ apps. No models
yet; `Profile`/`File` still live in expenses._

## Expenses

_TODO — the core domain: expenses, expense parts, payments, files, comments, and the user `Profile`._

## Invoices

_TODO — incoming/outgoing invoices; parallel in shape to expenses._

## Accounting

_TODO — pluggable "who may bookkeep what" layer (`AccountingPermissionProvider`); the concrete provider lives
in `cashflow.dauth`._

## Users

_TODO — user-facing endpoints, including current-user info and resolved permissions._

## Fortnox

_TODO — integration with the Fortnox bookkeeping API._