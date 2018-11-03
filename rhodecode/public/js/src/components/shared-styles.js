const styleElement = document.createElement('dom-module');
// this will use raw-loader
import sharedCSS from './style-polymer.css';

styleElement.innerHTML =
    `<template>
   <style>
   ${sharedCSS}
</style>
 </template>`;

styleElement.register('shared-styles');
