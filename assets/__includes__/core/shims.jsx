/*
*	Shims for features used by the core. The approximate minimum browser
*	requirement is IE 9. TODO: Really specify.
*/

//	document.head and .body.
if (!document.head) document.head = document.getElementsByTagName('head')[0];
onceReady(() => {
	if (!document.body) document.body = document.getElementsByTagName('body')[0];
});

//	Element.matches and querySelector.
Element.prototype.matches = Element.prototype.matches || Element.prototype.msMatchesSelector;

//	ParentNode.children.
(constructor => {
    if (constructor &&
        constructor.prototype &&
        constructor.prototype.children == null) {
        Object.defineProperty(constructor.prototype, 'children', {
            get: function() {
                let i = 0, node, nodes = this.childNodes, children = [];
                while (node = nodes[i++]) {
                    if (node.nodeType === 1) {
                        children.push(node);
                    }
                }
                return children;
            }
        });
    }
})(window.Node || window.Element);

//  console (I.E. without devtools)
window.console = window.console || {log: () => {}, warn: () => {}};
