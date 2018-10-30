const styleElement = document.createElement('dom-module');
import sharedCSS from 'raw-loader!./style-polymer.css';

styleElement.innerHTML =
    `<template>
   <style>
   ${sharedCSS}
</style>
 </template>`;

styleElement.register('shared-styles');
