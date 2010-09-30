/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>

@interface MGChartView : NSView <NSCopying>
{
    NSArray *data;
    NSString *title;
    NSString *currency;
    NSColor *backgroundColor;
    NSColor *titleColor;
}
- (void)setData:(NSArray *)aData;
- (void)setTitle:(NSString *)aTitle;
- (void)setCurrency:(NSString *)aCurrency;

@end