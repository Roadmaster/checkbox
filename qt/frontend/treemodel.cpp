#include "treemodel.h"
#include <QErrorMessage>
TreeModel::TreeModel() : m_messageBox(0) 
{

}

void TreeModel::warn()
{
    if (!m_messageBox)
        m_messageBox = new QErrorMessage();
    m_messageBox->showMessage("Unselecting a test will invalidate your submission for Ubuntu Friendly. If you plan to participate in Ubuntu Friendly, please, select all tests. You can always skip individual tests if you don't have the needed equipment.");
}

void TreeModel::changeAllChildren(QStandardItem *item, const QVariant &value, int role )
{
    QStandardItemModel::setData(item->index(), value, role);
    for(int i=0; i < item->rowCount(); i++) {
        QStandardItem *childItem = item->child(i);
        changeAllChildren(childItem, value, role);
    }
}

void TreeModel::enableAllChildren(bool enable, QStandardItem *item)
{
    item->setEnabled(enable);
    for(int i=0; i < item->rowCount(); i++) {
        QStandardItem *childItem = item->child(i);
 //       childItem->setEnabled(enable);
        enableAllChildren(enable, childItem);
    }
}

bool TreeModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
        QStandardItem *item = QStandardItemModel::itemFromIndex(index);
        if(!item)
            return false;

        // do not warn when the item is checked
        if ( value == QVariant(Qt::Unchecked) && role == Qt::CheckStateRole)
            warn();

        if (item->parent()) {
            QStandardItem *tmpItem = item;
            while (tmpItem->parent()) {
                QStandardItemModel::setData(item->index(), value, role);
                // we are a child, and we have to update parent's status
                int selected = 0;
                for(int i=0; i< tmpItem->parent()->rowCount(); i++) {
                    QStandardItem *childItem = tmpItem->parent()->child(i);
                    if (childItem->checkState() == Qt::Checked) {
                        selected++;
                    }
                }
                if (selected == tmpItem->parent()->rowCount()) {
                    tmpItem->parent()->setCheckState(Qt::Checked);
                } else if (selected == 0) {
                    tmpItem->parent()->setCheckState(Qt::Unchecked);
                } else {
                    tmpItem->parent()->setCheckState(Qt::PartiallyChecked);
                }
                tmpItem = tmpItem->parent();
            }
        }
        changeAllChildren(item, value, role);
        return QStandardItemModel::setData(index, value, role);
}

void TreeModel::setInteraction(bool value)
{
    for(int i=0; i< rowCount(); i++) {
        QStandardItem  *item = this->item(i, 0);
        if(!item)
            continue;
        enableAllChildren(value, item);
    }
}

void TreeModel::selectAll(bool select)
{
    Qt::CheckState state = select ? Qt::Checked : Qt::Unchecked;
    for(int i=0; i< rowCount(); i++) {
        QStandardItem *item = this->item(i, 0);
        if(!item)
            continue;
        changeAllChildren(item, state, Qt::CheckStateRole);
    }
}
