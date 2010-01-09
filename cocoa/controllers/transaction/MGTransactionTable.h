/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "HS" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/hs_license
*/

#import <Cocoa/Cocoa.h>
#import "HSTableColumnManager.h"
#import "MGDocument.h"
#import "PyTransactionTable.h"
#import "MGEditableTable.h"
#import "MGTableView.h"
#import "MGFieldEditor.h"
#import "MGDateFieldEditor.h"

@interface MGTransactionTable : MGEditableTable 
{
    HSTableColumnManager *columnsManager;
    MGFieldEditor *customFieldEditor;
    MGDateFieldEditor *customDateFieldEditor;
}
- (id)initWithDocument:(MGDocument *)aDocument view:(MGTableView *)aTableView;

/* Public */
- (PyTransactionTable *)py;
- (id)fieldEditorForObject:(id)asker;
- (void)showFromAccount:(id)sender;
- (void)showToAccount:(id)sender;
@end