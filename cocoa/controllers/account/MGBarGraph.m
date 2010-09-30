/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import "MGBarGraph.h"

@implementation MGBarGraph
- (id)initWithPyParent:(id)aPyParent pyClassName:(NSString *)aClassName
{
    self = [super initWithPyClassName:aClassName pyParent:aPyParent];
    view = [[MGBarGraphView alloc] init];
    return self;
}

- (void)dealloc
{
    [view release];
    [super dealloc];
}

@end
