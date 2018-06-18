/*
*	Shims for features used by the core. The approximate minimum browser
*	requirement is IE 9. TODO: Really specify.
*/

if (!document.head) document.head = document.getElementsByTagName('head')[0];
Element.matches = Element.matches || Element.msMatchesSelector;
